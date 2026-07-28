/**
 * State Store Module for UI Request Adapter (WP-2)
 *
 * Manages request states, plan storage, staleness checks, and atomic state updates.
 */

import {
  RequestAbortedError,
  RequestTimeoutError,
  StaleResponseError
} from './error_handling.js';

export const RequestState = {
  IDLE: 'IDLE',
  LOADING: 'LOADING',
  RETRYING: 'RETRYING',
  SUCCESS: 'SUCCESS',
  ERROR: 'ERROR',
  ABORTED: 'ABORTED',
  STALE: 'STALE'
};

export class StateStore {
  constructor() {
    this.state = RequestState.IDLE;
    this.activeRequestId = null;
    this.sourceRevision = null;
    this.retryCount = 0;
    this.appliedPlan = null;
    this.provenance = null;
    this.lastError = null;
    this._isAborted = false;
  }

  isBusy() {
    return this.state === RequestState.LOADING || this.state === RequestState.RETRYING;
  }

  startRequest(requestId, sourceRevision) {
    this.activeRequestId = requestId;
    this.sourceRevision = sourceRevision;
    this.retryCount = 0;
    this.lastError = null;
    this._isAborted = false;
    this.state = RequestState.LOADING;
  }

  updateRetry(retryCount) {
    if (this._isAborted || this.state === RequestState.ABORTED) return;
    this.retryCount = retryCount;
    this.state = RequestState.RETRYING;
  }

  validateStaleGuard(requestId, sourceRevision) {
    if (this._isAborted || this.state === RequestState.ABORTED) {
      return { isValid: false, reason: 'Request was aborted' };
    }
    if (Number(requestId) !== Number(this.activeRequestId)) {
      return { isValid: false, reason: `Request ID mismatch: received ${requestId}, expected ${this.activeRequestId}` };
    }
    if (sourceRevision !== this.sourceRevision) {
      return { isValid: false, reason: `Source revision mismatch: received ${sourceRevision}, expected ${this.sourceRevision}` };
    }
    if (this.state !== RequestState.LOADING && this.state !== RequestState.RETRYING) {
      return { isValid: false, reason: `State inactive for response: current state is ${this.state}` };
    }
    return { isValid: true, reason: null };
  }

  acceptPlan(requestId, sourceRevision, plan, provenance) {
    const { isValid, reason } = this.validateStaleGuard(requestId, sourceRevision);
    if (!isValid) {
      this.state = RequestState.STALE;
      this.lastError = new StaleResponseError(`Stale response discarded: ${reason}`, {
        receivedRequestId: requestId,
        expectedRequestId: this.activeRequestId,
        receivedRevision: sourceRevision,
        expectedRevision: this.sourceRevision
      });
      return { accepted: false, reason };
    }

    this.appliedPlan = plan;
    this.provenance = provenance;
    this.state = RequestState.SUCCESS;
    this.lastError = null;
    return { accepted: true, reason: null };
  }

  failRequest(requestId, error) {
    if (Number(requestId) !== Number(this.activeRequestId)) {
      return; // Ignore obsolete inactive failures
    }

    this.lastError = error;
    if (error instanceof RequestAbortedError || error?.name === 'AbortError' || this._isAborted) {
      this.state = RequestState.ABORTED;
    } else if (error instanceof RequestTimeoutError) {
      this.state = RequestState.ERROR;
    } else {
      this.state = RequestState.ERROR;
    }
  }

  abortRequest() {
    this._isAborted = true;
    this.state = RequestState.ABORTED;
    this.lastError = new RequestAbortedError(
      'Request aborted by user or state change',
      this.activeRequestId
    );
  }

  reset() {
    this.state = RequestState.IDLE;
    this.activeRequestId = null;
    this.sourceRevision = null;
    this.retryCount = 0;
    this.appliedPlan = null;
    this.provenance = null;
    this.lastError = null;
    this._isAborted = false;
  }
}
