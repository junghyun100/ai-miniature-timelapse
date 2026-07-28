/**
 * Fetch Wrapper Module for UI Request Adapter (WP-2)
 *
 * Provides fetch execution with timeout, abort cancellation, exponential retry,
 * and error sanitization per Section 14.4.
 */

import {
  HttpError,
  RequestAbortedError,
  RequestTimeoutError,
  RetryExhaustedError,
  isRetryableError
} from './error_handling.js';

export class FetchWrapper {
  constructor({
    defaultTimeoutMs = 60000,
    maxRetries = 2,
    retryBackoffBaseMs = 100,
    fetchFn = null
  } = {}) {
    this.defaultTimeoutMs = defaultTimeoutMs;
    this.maxRetries = maxRetries;
    this.retryBackoffBaseMs = retryBackoffBaseMs;
    this.fetchFn = fetchFn || (typeof fetch !== 'undefined' ? fetch.bind(window) : null);
  }

  async fetchJson({
    url,
    method = 'POST',
    body = null,
    headers = {},
    requestId = null,
    timeoutMs = null,
    externalSignal = null,
    onRetry = null
  }) {
    const effectiveTimeout = timeoutMs !== null ? timeoutMs : this.defaultTimeoutMs;
    let attempt = 0;
    let lastError = null;

    while (attempt <= this.maxRetries) {
      if (externalSignal?.aborted) {
        throw new RequestAbortedError(`Request ${requestId} aborted before attempt ${attempt + 1}`, requestId);
      }

      try {
        const result = await this._singleAttempt({
          url,
          method,
          body,
          headers,
          effectiveTimeout,
          externalSignal
        });
        return result;
      } catch (err) {
        lastError = err;

        if (!isRetryableError(err) || attempt >= this.maxRetries) {
          if (attempt > 0 && isRetryableError(err)) {
            throw new RetryExhaustedError(
              `Request failed after ${attempt + 1} attempts: ${err.message}`,
              attempt + 1,
              err
            );
          }
          throw err;
        }

        attempt++;
        if (typeof onRetry === 'function') {
          onRetry(attempt, err);
        }

        const delay = this.retryBackoffBaseMs * Math.pow(2, attempt - 1);
        await this._delayWithAbort(delay, externalSignal);
      }
    }

    if (lastError) throw lastError;
    throw new HttpError('Unknown fetch error', 500);
  }

  async _singleAttempt({ url, method, body, headers, effectiveTimeout, externalSignal }) {
    const controller = new AbortController();
    let timeoutId = null;

    const onExternalAbort = () => {
      controller.abort();
    };

    if (externalSignal) {
      if (externalSignal.aborted) {
        throw new RequestAbortedError('Request was aborted');
      }
      externalSignal.addEventListener('abort', onExternalAbort);
    }

    let isTimedOut = false;
    if (effectiveTimeout > 0) {
      timeoutId = setTimeout(() => {
        isTimedOut = true;
        controller.abort();
      }, effectiveTimeout);
    }

    try {
      const fetchImpl = this.fetchFn || globalThis.fetch;
      if (!fetchImpl) {
        throw new Error('No fetch implementation available');
      }

      const response = await fetchImpl(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...headers
        },
        body: body ? (typeof body === 'string' ? body : JSON.stringify(body)) : null,
        signal: controller.signal
      });

      if (timeoutId) clearTimeout(timeoutId);
      if (externalSignal) externalSignal.removeEventListener('abort', onExternalAbort);

      if (!response.ok) {
        const text = await response.text().catch(() => '');
        throw new HttpError(`HTTP ${response.status}: ${response.statusText}`, response.status, text);
      }

      return await response.json();
    } catch (err) {
      if (timeoutId) clearTimeout(timeoutId);
      if (externalSignal) externalSignal.removeEventListener('abort', onExternalAbort);

      if (isTimedOut) {
        throw new RequestTimeoutError(`Client timeout of ${effectiveTimeout / 1000}s exceeded`, effectiveTimeout / 1000);
      }
      if (externalSignal?.aborted || err.name === 'AbortError') {
        throw new RequestAbortedError('Request was aborted during network call');
      }
      throw err;
    }
  }

  _delayWithAbort(ms, externalSignal) {
    return new Promise((resolve, reject) => {
      if (externalSignal?.aborted) {
        return reject(new RequestAbortedError('Aborted during retry delay'));
      }
      const timer = setTimeout(() => {
        if (externalSignal) externalSignal.removeEventListener('abort', onAbort);
        resolve();
      }, ms);

      const onAbort = () => {
        clearTimeout(timer);
        reject(new RequestAbortedError('Aborted during retry delay'));
      };

      if (externalSignal) {
        externalSignal.addEventListener('abort', onAbort, { once: true });
      }
    });
  }
}
