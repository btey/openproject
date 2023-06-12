//-- copyright
// OpenProject is an open source project management software.
// Copyright (C) 2021 Ben Tey
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License version 3.
//
// OpenProject is a fork of ChiliProject, which is a fork of Redmine. The copyright follows:
// Copyright (C) 2006-2013 Jean-Philippe Lang
// Copyright (C) 2010-2013 the ChiliProject Team
// Copyright (C) 2012-2021 the OpenProject GmbH
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
//
// See docs/COPYRIGHT.rdoc for more details.
//++

import {
  ChangeDetectionStrategy,
  Component,
  HostBinding,
  Input,
} from '@angular/core';
import { PathHelperService } from 'core-app/core/path-helper/path-helper.service';
import { I18nService } from 'core-app/core/i18n/i18n.service';
import {
  IGitlabPipelineResource,
  IGitlabMergeRequest,
} from 'core-app/features/plugins/linked/openproject-gitlab_integration/state/gitlab-merge-request.model';

@Component({
  selector: 'op-gitlab-merge-request',
  templateUrl: './merge-request.component.html',
  styleUrls: [
    './merge-request.component.sass',
    './mr-pipeline.component.sass',
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})

export class MergeRequestComponent {
  @HostBinding('class.op-merge-request') className = true;

  @Input() public mergeRequest:IGitlabMergeRequest;

  public text = {
    label_created_by: this.I18n.t('js.label_created_by'),
    label_last_updated_on: this.I18n.t('js.label_last_updated_on'),
    label_details: this.I18n.t('js.label_details'),
    label_pipelines: this.I18n.t('js.gitlab_integration.gitlab_pipelines'),
  };

  constructor(
    readonly PathHelper:PathHelperService,
    readonly I18n:I18nService,
  ) {
  }

  get state():string {
    if (this.mergeRequest.state === 'opened') {
      return (this.mergeRequest.draft ? 'open' : 'ready');
    } else {
      return(this.mergeRequest.merged ? 'merged' : 'closed');
    }
  }

  public pipelineStateText(pipeline:IGitlabPipelineResource) {
    return(pipeline.status);
  }

  public pipelineState(pipeline:IGitlabPipelineResource) {
    return(pipeline.status);
  }

  public pipelineStateIcon(pipeline:IGitlabPipelineResource) {
    switch (this.pipelineState(pipeline)) {
      case 'success': {
        return 'checkmark'
      }
      case 'queued': {
        return 'getting-started'
      }
      case 'running': {
        return 'loading1'
      }
      case 'failed': {
        return 'cancel'
      }
      case 'timed_out': {
        return 'reminder'
      }
      case 'action_required': {
        return 'warning'
      }
      case 'stale': {
        return 'not-supported'
      }
      case 'skipped': {
        return 'redo'
      }
      case 'neutral': {
        return 'minus1'
      }
      case 'cancelled': {
        return 'minus1'
      }
      default: {
        return 'not-supported'
      }
    }
  }
}
