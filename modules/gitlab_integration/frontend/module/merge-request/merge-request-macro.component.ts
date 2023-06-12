// -- copyright
// OpenProject is an open source project management software.
// Copyright (C) 2012-2023 the OpenProject GmbH
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License version 3.
//
// OpenProject is a fork of ChiliProject, which is a fork of Redmine. The copyright follows:
// Copyright (C) 2006-2013 Jean-Philippe Lang
// Copyright (C) 2010-2013 the ChiliProject Team
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
// See COPYRIGHT and LICENSE files for more details.
// ++    Ng1FieldControlsWrapper,

import {
    ChangeDetectionStrategy,
    Component,
    ElementRef,
    Injector,
    Input,
    OnInit,
  } from '@angular/core';
  import { HalResourceEditingService } from 'core-app/shared/components/fields/edit/services/hal-resource-editing.service';
  import { populateInputsFromDataset } from 'core-app/shared/components/dataset-inputs';
  import { IGitlabMergeRequest } from '../state/gitlab-merge-request.model';
  import { GitlabMergeRequestResourceService } from '../state/gitlab-merge-request.service';
  import { Observable } from 'rxjs';
  import { map } from 'rxjs/operators';
  import { I18nService } from 'core-app/core/i18n/i18n.service';
  import { MergeRequestState } from './merge-request-state.component';
  
  export const gitlabMergeRequestMacroSelector = 'macro.gitlab_merge_request';
  
  @Component({
    selector: gitlabMergeRequestMacroSelector,
    templateUrl: './merge-request-macro.component.html',
    styleUrls: ['./merge-request-macro.component.sass'],
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [
      HalResourceEditingService,
    ],
  })
  export class MergeRequestMacroComponent implements OnInit {
    @Input() MergeRequestId:string;
  
    @Input() MergeRequestState:MergeRequestState;
  
    mergeRequest$:Observable<IGitlabMergeRequest>;
  
    displayText$:Observable<string>;
  
    constructor(
      readonly elementRef:ElementRef,
      readonly injector:Injector,
      readonly mergeRequests:GitlabMergeRequestResourceService,
      readonly I18n:I18nService,
    ) {
      populateInputsFromDataset(this);
    }
  
    ngOnInit() {
      this.mergeRequest$ = this
        .mergeRequests
        .requireSingle(this.mergeRequestId);
  
      this.displayText$ = this
        .mergeRequest$
        .pipe(
          map((mr) => this.buildText(mr)),
        );
    }
  
    private buildText(pr:IGitlabMergeRequest):string {
      const gitlabUserLink = this.htmlLink(mr._embedded.gitlabUser.htmlUrl, mr._embedded.gitlabUser.login);
      const repositoryLink = this.htmlLink(mr.repositoryHtmlUrl, mr.repository);
      const mrLink = this.htmlLink(mr.htmlUrl, mr.title);
  
      const message = this.mergeRequestState === 'referenced' ? 'referenced_message' : 'message';
      return this.I18n.t(
        `js.gitlab_integration.merge_requests.${message}`,
        {
          mr_number: mr.number,
          mr_link: mrLink,
          repository_link: repositoryLink,
          mr_state: this.I18n.t(
            `js.gitlab_integration.merge_requests.states.${this.mergeRequestState}`,
            { defaultValue: this.mergeRequestState || '(unknown state)' },
          ),
          gitlab_user_link: gitlabUserLink,
        },
      );
    }
  
    private htmlLink(href:string, title:string):string {
      const link = document.createElement('a');
      link.href = href;
      link.textContent = title;
  
      return link.outerHTML;
    }
  }