/**
 * UI Request Adapter Module (WP-2)
 *
 * High-level UI request adapter integrating monotonic request IDs,
 * timeout/abort controllers, exponential retry policy, stale guard discard,
 * loading state separation, and provenance tracking per Section 14.4 and Section 14.6.
 */

import { FetchWrapper } from './fetch_wrapper.js';
import { StateStore, RequestState } from './state_store.js';
import { ProvenanceModel, ProvenanceSource } from './provenance_model.js';
import { sanitizeErrorMessage, RequestAdapterError } from './error_handling.js';
import { computeSourceRevisionSync } from './source_revision.js';

export class UIRequestAdapter {
  constructor({ fetchWrapper = null, state_store = null, computeRevisionFn = null } = {}) {
    this.fetchWrapper = fetchWrapper || new FetchWrapper();
    this.stateStore = state_store || new StateStore();
    this._requestIdCounter = 0;
    this._activeController = null;
    this._currentDraft = null;
    this.computeRevisionFn = computeRevisionFn || this._defaultComputeRevision;
  }

  getNextRequestId() {
    this._requestIdCounter += 1;
    return this._requestIdCounter;
  }

  getLoadingState() {
    return this.stateStore.state;
  }

  getAppliedPlan() {
    return this.stateStore.appliedPlan;
  }

  getProvenance() {
    return this.stateStore.provenance;
  }

  getActiveRequestId() {
    return this.stateStore.activeRequestId;
  }

  getSourceRevision() {
    return this.stateStore.sourceRevision;
  }

  cancelActiveRequest() {
    if (this._activeController) {
      this._activeController.abort();
      this._activeController = null;
    }
    this.stateStore.abortRequest();
  }

  onDraftChange(newDraft) {
    if (this.stateStore.isBusy()) {
      this.cancelActiveRequest();
    }
    this._currentDraft = newDraft;
    return this.computeRevisionFn(newDraft);
  }

  async executeRequest({
    url,
    payload = {},
    draft = {},
    headers = {},
    timeoutMs = null,
    modelId = null,
    baseUrlLabel = null
  }) {
    // 1. Monotonic Request ID
    const requestId = this.getNextRequestId();

    // 2. Source Revision
    this._currentDraft = draft;
    const sourceRevision = this.computeRevisionFn(draft);

    // 3. Abort previous in-flight request
    if (this.stateStore.isBusy()) {
      this.cancelActiveRequest();
    }

    // 4. Create AbortController & start request
    const controller = new AbortController();
    this._activeController = controller;
    this.stateStore.startRequest(requestId, sourceRevision);

    const reqPayload = {
      ...payload,
      request_id: String(requestId),
      source_revision: sourceRevision
    };

    const onRetry = (attempt) => {
      this.stateStore.updateRetry(attempt);
    };

    try {
      // 5. Fetch
      const responseData = await this.fetchWrapper.fetchJson({
        url,
        method: 'POST',
        body: reqPayload,
        headers,
        requestId,
        timeoutMs,
        externalSignal: controller.signal,
        onRetry
      });

      const resReqId = responseData?.request_id ? Number(responseData.request_id) : requestId;
      const resRevision = responseData?.source_revision || sourceRevision;

      // Build Provenance
      const provenance = ProvenanceModel.fromNimResponse(responseData, requestId, sourceRevision);
      if (modelId) provenance.model_id = modelId;
      if (baseUrlLabel) provenance.base_url_label = baseUrlLabel;

      // 6. Stale Guard check & Atomic Plan Application
      const result = this.stateStore.acceptPlan(
        resReqId,
        resRevision,
        responseData,
        provenance
      );

      if (!result.accepted) {
        return {
          success: false,
          stale: true,
          reason: result.reason,
          state: this.stateStore.state
        };
      }

      return {
        success: true,
        request_id: requestId,
        source_revision: sourceRevision,
        plan: this.stateStore.appliedPlan,
        provenance: this.stateStore.provenance ? this.stateStore.provenance.toDict() : null,
        state: this.stateStore.state
      };

    } catch (err) {
      // Failure Rules enforcement
      const wrappedError = err instanceof RequestAdapterError
        ? err
        : new RequestAdapterError(err.message);

      this.stateStore.failRequest(requestId, wrappedError);

      return {
        success: false,
        error: sanitizeErrorMessage(err.message),
        error_type: err.name || 'Error',
        state: this.stateStore.state
      };
    } finally {
      if (this._activeController === controller) {
        this._activeController = null;
      }
    }
  }

  _defaultComputeRevision(draft) {
    if (!draft) return 'sha256:empty';
    if (typeof draft === 'string') return `sha256:${draft}`;
    try {
      return computeSourceRevisionSync(draft);
    } catch {
      return 'sha256:unknown';
    }
  }
}
