/**
 * Error Handling Module for UI Request Adapter (WP-2)
 *
 * Defines structured error types, sanitization, and retryability rules per Section 14.4.
 */

export function sanitizeErrorMessage(msg) {
  if (!msg || typeof msg !== 'string') return '';
  let sanitized = msg.replace(/nvapi-[A-Za-z0-9_-]+/g, '[REDACTED_API_KEY]');
  sanitized = sanitized.replace(/(?:Bearer|key|token|secret)\s*[:=]\s*["']?[A-Za-z0-9._-]+["']?/gi, '[REDACTED_SECRET]');
  return sanitized;
}

export class RequestAdapterError extends Error {
  constructor(message, details = null) {
    const sanitized = sanitizeErrorMessage(message);
    super(sanitized);
    this.name = 'RequestAdapterError';
    this.message = sanitized;
    this.details = details;
  }
}

export class RequestTimeoutError extends RequestAdapterError {
  constructor(message, timeoutSeconds = 60.0, requestId = null) {
    super(message, { timeoutSeconds, requestId });
    this.name = 'RequestTimeoutError';
    this.timeoutSeconds = timeoutSeconds;
    this.requestId = requestId;
  }
}

export class RequestAbortedError extends RequestAdapterError {
  constructor(message = 'Request was cancelled', requestId = null) {
    super(message, { requestId });
    this.name = 'RequestAbortedError';
    this.requestId = requestId;
  }
}

export class StaleResponseError extends RequestAdapterError {
  constructor(message, details = {}) {
    super(message, details);
    this.name = 'StaleResponseError';
    this.receivedRequestId = details.receivedRequestId;
    this.expectedRequestId = details.expectedRequestId;
    this.receivedRevision = details.receivedRevision;
    this.expectedRevision = details.expectedRevision;
  }
}

export class HttpError extends RequestAdapterError {
  constructor(message, statusCode, responseBody = null) {
    super(message, { statusCode, body: responseBody });
    this.name = 'HttpError';
    this.statusCode = statusCode;
    this.responseBody = responseBody;
  }
}

export class RetryExhaustedError extends RequestAdapterError {
  constructor(message, attempts, lastError) {
    super(message, { attempts, lastError: lastError?.message });
    this.name = 'RetryExhaustedError';
    this.attempts = attempts;
    this.lastError = lastError;
  }
}

export const RETRYABLE_HTTP_CODES = new Set([429, 500, 502, 503, 504]);
export const NON_RETRYABLE_HTTP_CODES = new Set([400, 401, 403, 404]);

export function isRetryableStatus(statusCode) {
  return RETRYABLE_HTTP_CODES.has(statusCode);
}

export function isRetryableError(error) {
  if (
    error instanceof RequestTimeoutError ||
    error instanceof RequestAbortedError ||
    error instanceof StaleResponseError ||
    error?.name === 'AbortError'
  ) {
    return false;
  }
  if (error instanceof HttpError) {
    return isRetryableStatus(error.statusCode);
  }
  return true; // Network or connection error
}
