import { EntityStore, StoreConfig } from '@datorama/akita';
import { IGitlabMergeRequest } from 'core-app/features/plugins/linked/openproject-gitlab_integration/state/gitlab-merge-request.model';
import {
  createInitialResourceState,
  ResourceState,
} from 'core-app/core/state/resource-store';

export interface GitlabMergeRequestsState extends ResourceState<IGitlabMergeRequest> {
}

@StoreConfig({ name: 'gitlab-merge-requests' })
export class GitlabMergeRequestsStore extends EntityStore<GitlabMergeRequestsState> {
  constructor() {
    super(createInitialResourceState());
  }
}