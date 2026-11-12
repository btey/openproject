//-- copyright
// OpenProject is an open source project management software.
// Copyright (C) 2023 Ben Tey
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License version 3.
//
// OpenProject is a fork of ChiliProject, which is a fork of Redmine. The copyright follows:
// Copyright (C) 2006-2013 Jean-Philippe Lang
// Copyright (C) 2010-2013 the ChiliProject Team
// Copyright (C) the OpenProject GmbH
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

import { Component, Input, inject, ChangeDetectionStrategy, Output, EventEmitter } from '@angular/core';
import { PathHelperService } from 'core-app/core/path-helper/path-helper.service';
import { I18nService } from 'core-app/core/i18n/i18n.service';
import {IGitlabIssueResource} from 'core-app/features/plugins/linked/openproject-gitlab_integration/typings';
import { HttpClient } from '@angular/common/http';
import { ToastService } from 'core-app/shared/components/toaster/toast.service';

@Component({
  selector: 'gitlab-issue',
  templateUrl: './issue.component.html',
  styleUrls: [
    './issue.component.sass',
  ],
  host: { class: 'op-issue' },
  changeDetection: ChangeDetectionStrategy.Eager,
  standalone: false,
})

export class IssueComponent {
  readonly PathHelper = inject(PathHelperService);
  readonly I18n = inject(I18nService);
  readonly httpClient = inject(HttpClient);
  readonly toastService = inject(ToastService);

  @Input() public gitlabIssue:IGitlabIssueResource;
  @Output() public deleted = new EventEmitter<void>();

  public text = {
    label_created_by: this.I18n.t('js.label_created_by'),
    label_last_updated_on: this.I18n.t('js.gitlab_integration.updated_on'),
    label_details: this.I18n.t('js.label_details'),
    label_unlink: this.I18n.t('js.label_unlink'),
    confirm_delete: this.I18n.t('js.gitlab_integration.confirm_unlink_issue'),
  };

  get state() {

    if (this.gitlabIssue.state === 'opened') {
      return ('open');
    } else {
      return('closed');
    }
  }

  get hasDeletePermission():boolean {
    return !!(this.gitlabIssue as any)._links?.delete;
  }

  toggleLabels(identifier: string) {
    const labelsElement = document.querySelector(`.op-issue--labels-${identifier}`) as HTMLElement;

    // Check the current display property and toggle it
    labelsElement.style.display = labelsElement.style.display === 'none' ? 'block' : 'none';
  }

  deleteIssue():void {
    const confirmMessage = this.I18n.t('js.gitlab_integration.confirm_unlink_issue', { number: `#${this.gitlabIssue.number}` });

    if (confirm(confirmMessage)) {
      const deleteUrl = (this.gitlabIssue as any)._links?.delete?.href;

      if (!deleteUrl) {
        console.error('Delete URL not found in issue links:', this.gitlabIssue);
        console.error('Available _links:', (this.gitlabIssue as any)._links);
        this.toastService.addError(this.I18n.t('js.gitlab_integration.unlink_error'));
        return;
      }

      console.log('Attempting to delete issue via:', deleteUrl);

      this.httpClient.delete(deleteUrl).subscribe({
        next: () => {
          console.log('Delete successful');
          this.toastService.addSuccess(this.I18n.t('js.gitlab_integration.unlink_success'));
          this.deleted.emit();
        },
        error: (error) => {
          console.error('Delete failed with error:', error);
          console.error('Error status:', error.status);
          console.error('Error message:', error.message);
          console.error('Error body:', error.error);
          this.toastService.addError(this.I18n.t('js.gitlab_integration.unlink_error'));
        }
      });
    }
  }
}
