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

import { Component, Input, inject, ChangeDetectionStrategy, OnInit, OnDestroy, OnChanges, SimpleChanges, ChangeDetectorRef } from '@angular/core';
import { WorkPackageResource } from "core-app/features/hal/resources/work-package-resource";
import { I18nService } from "core-app/core/i18n/i18n.service";
// Create MR feature — Start
import { ToastService } from "core-app/shared/components/toaster/toast.service";
import { GitlabMergeRequestService } from "../gitlab-merge-request.service";
import { HttpClient } from '@angular/common/http';
import { PathHelperService } from 'core-app/core/path-helper/path-helper.service';
import { GitlabConfigurationService } from '../gitlab-configuration.service';
import { Subscription } from 'rxjs';
import { LinkType } from '../link-type-menu/link-type-menu.component';
// Create MR feature — End

@Component({
  selector: 'tab-header-mr',
  templateUrl: './tab-header-mr.template.html',
  styleUrls: [
    './styles/tab-header-mr.sass'
  ],
  changeDetection: ChangeDetectionStrategy.Eager,
  standalone: false,
})
export class TabHeaderMrsComponent implements OnInit, OnDestroy, OnChanges {
  readonly I18n = inject(I18nService);
  private gitlabMrService = inject(GitlabMergeRequestService);
  private toastService = inject(ToastService);
  private http = inject(HttpClient);
  private pathHelper = inject(PathHelperService);
  private gitlabConfigService = inject(GitlabConfigurationService);
  private cdr = inject(ChangeDetectorRef);

  @Input() public workPackage:WorkPackageResource;

  // Create MR feature — Start
  public isCreatingMr = false;
  public linkType:LinkType = 'public';
  public isGitlabConfigured = false;

  private configSubscription?: Subscription;
  // Create MR feature — End

  public text = {
    title: this.I18n.t('js.gitlab_integration.tab_header_mr.title'),
    // Create MR feature — Start
    createMrButtonLabel: this.I18n.t('js.gitlab_integration.tab_header_mr.create_mr.label'),
    createMrButtonDescription: this.I18n.t('js.gitlab_integration.tab_header_mr.create_mr.description'),
    // Create MR feature — End
    gitMenuLabel: this.I18n.t('js.gitlab_integration.tab_header_mr.copy_menu.label'),
    gitMenuDescription: this.I18n.t('js.gitlab_integration.tab_header_mr.copy_menu.description'),
    // Create MR feature — Start
    createMrLoading: this.I18n.t('js.gitlab_integration.tab_header_mr.create_mr.loading'),
    createMrSuccess: this.I18n.t('js.gitlab_integration.tab_header_mr.create_mr.success'),
    createMrError: (error:string) => this.I18n.t('js.gitlab_integration.tab_header_mr.create_mr.error', { error }),
    toggleLinkTypeDescription: this.I18n.t('js.gitlab_integration.tab_header_mr.create_mr.toggle_link_type_description'),
    publicLink: this.I18n.t('js.gitlab_integration.link_type_menu.public_link'),
    privateLink: this.I18n.t('js.gitlab_integration.link_type_menu.private_link'),
    // Create MR feature — End
  };

  // Create MR feature — Start
  ngOnInit():void {
    this.checkGitlabConfiguration();

    // Subscribe to configuration updates
    this.configSubscription = this.gitlabConfigService.onConfigurationUpdated$.subscribe(() => {
      console.log('[MR Header] Configuration updated, re-checking...');
      this.checkGitlabConfiguration();
    });
  }

  ngOnChanges(changes: SimpleChanges):void {
    // Re-check configuration when work package changes
    if (changes['workPackage'] && !changes['workPackage'].firstChange) {
      console.log('[MR Header] Work package changed, re-checking configuration...');
      this.checkGitlabConfiguration();
    }
  }

  ngOnDestroy():void {
    // Clean up subscription
    this.configSubscription?.unsubscribe();
  }

  checkGitlabConfiguration():void {
    const projectId = this.workPackage.project.id;
    const apiUrl = `${this.pathHelper.api.v3.apiV3Base}/projects/${projectId}/gitlab_configuration`;

    this.http.get<any>(apiUrl).subscribe({
      next: (config) => {
        // Check if GitLab is configured (has URL, project identifier, and access token)
        this.isGitlabConfigured = !!(
          config.gitlabUrl &&
          config.projectIdentifier &&
          config.accessTokenPresent
        );
        // Force change detection to update the view immediately
        this.cdr.detectChanges();
      },
      error: () => {
        this.isGitlabConfigured = false;
        // Force change detection even on error
        this.cdr.detectChanges();
      }
    });
  }

  public toggleLinkType(event:MouseEvent):void {
    event.stopPropagation(); // Prevent button's click from firing
    this.linkType = this.linkType === 'public' ? 'private' : 'public';
  }

  public createMergeRequest():void {
    this.isCreatingMr = true;
    const usePrivateLink = this.linkType === 'private';

    this.gitlabMrService.createMergeRequest(this.workPackage.displayId!, usePrivateLink)
      .subscribe({
        next: (response) => {
          // Reset button state immediately
          this.isCreatingMr = false;

          // Show success message
          this.toastService.addSuccess(this.text.createMrSuccess);

          // If response contains web_url, open it in a new tab
          if (response.web_url) {
            window.open(response.web_url, '_blank');
          }

          // Refresh the MR list after a delay (allows user to see success state)
          setTimeout(() => window.location.reload(), 2000);
        },
        error: (error) => {
          this.isCreatingMr = false;
          const errorMessage = error?.error?.message || error?.message || 'Unknown error';
          this.toastService.addError(this.text.createMrError(errorMessage));
        }
      });
  }
  // Create MR feature — End
}
