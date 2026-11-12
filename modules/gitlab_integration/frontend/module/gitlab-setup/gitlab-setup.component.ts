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

import { Component, Input, OnInit, OnChanges, SimpleChanges, ChangeDetectorRef } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { WorkPackageResource } from 'core-app/features/hal/resources/work-package-resource';
import { I18nService } from 'core-app/core/i18n/i18n.service';
import { PathHelperService } from 'core-app/core/path-helper/path-helper.service';
import { GitlabConfigurationService } from '../gitlab-configuration.service';

interface GitlabConfiguration {
  id: number;
  projectId: number;
  gitlabUrl: string | null;
  projectIdentifier: string | null;
  accessTokenPresent: boolean;
}

@Component({
  selector: 'gitlab-setup',
  templateUrl: './gitlab-setup.template.html',
  styleUrls: ['./gitlab-setup.component.sass'],
  standalone: false,
})
export class GitlabSetupComponent implements OnInit, OnChanges {
  @Input() public workPackage:WorkPackageResource;

  public showForm = false;
  public gitlabUrl = '';
  public projectIdentifier = '';
  public accessToken = '';
  public accessTokenPlaceholder = '';
  public saving = false;
  public message = '';
  public messageType:'success'|'error'|'' = '';
  public canManage = false;

  public text = {
    showSetup: this.I18n.t('js.gitlab_integration.gitlab_setup.show'),
    hideSetup: this.I18n.t('js.gitlab_integration.gitlab_setup.hide'),
  };

  constructor(
    private http:HttpClient,
    private cdr:ChangeDetectorRef,
    private gitlabConfigService:GitlabConfigurationService,
    readonly I18n:I18nService,
    readonly PathHelper:PathHelperService,
  ) {}

  ngOnInit():void {
    this.checkPermissions();
    this.loadConfiguration();
  }

  ngOnChanges(changes: SimpleChanges):void {
    // Re-check permissions and reload configuration when work package changes
    if (changes['workPackage'] && !changes['workPackage'].firstChange) {
      console.log('[GitLab Setup] Work package changed, re-checking permissions...');
      this.checkPermissions();
      this.loadConfiguration();
    }
  }

  checkPermissions():void {
    // Check if user has the manage_gitlab_configuration permission
    // This is exposed via a HAL link on the work package resource
    this.canManage = !!(this.workPackage.manageGitlabConfiguration);
    // Force change detection to update button visibility immediately
    this.cdr.detectChanges();
  }

  loadConfiguration():void {
    const projectId = this.workPackage.project.id;
    const apiUrl = `${this.PathHelper.api.v3.apiV3Base}/projects/${projectId}/gitlab_configuration`;

    this.http.get<GitlabConfiguration>(apiUrl).subscribe({
      next: (config) => {
        console.log('Loaded configuration:', config);
        // API returns camelCase properties due to CamelCasingStrategy
        this.gitlabUrl = config.gitlabUrl ?? '';
        this.projectIdentifier = config.projectIdentifier ?? '';
        if (config.accessTokenPresent) {
          this.accessTokenPlaceholder = '••••••••••••••••';
        } else {
          this.accessTokenPlaceholder = '';
        }
        // Clear the access token field since we never load the actual token
        this.accessToken = '';
      },
      error: (error) => {
        console.error('Failed to load GitLab configuration:', error);
        this.showMessage('Failed to load GitLab configuration', 'error');
      },
    });
  }

  toggleForm():void {
    this.showForm = !this.showForm;
  }

  save():void {
    const projectId = this.workPackage.project.id;
    const apiUrl = `${this.PathHelper.api.v3.apiV3Base}/projects/${projectId}/gitlab_configuration`;

    const data:any = {
      gitlab_url: this.gitlabUrl.trim(),
      project_identifier: this.projectIdentifier.trim(),
    };

    // Only include access token if it's been entered
    if (this.accessToken && this.accessToken !== this.accessTokenPlaceholder) {
      data.access_token = this.accessToken;
    }

    console.log('[GitLab Setup] Starting save at:', new Date().toISOString());
    this.saving = true;
    this.message = '';
    this.messageType = '';
    this.cdr.detectChanges(); // Force UI update to show "Saving..."

    const startTime = Date.now();

    this.http.patch<GitlabConfiguration>(apiUrl, data).subscribe({
      next: (config) => {
        const duration = Date.now() - startTime;
        console.log(`[GitLab Setup] Save completed in ${duration}ms at:`, new Date().toISOString());
        console.log('Saved configuration:', config);

        // Update form with saved values (API returns camelCase)
        this.gitlabUrl = config.gitlabUrl ?? '';
        this.projectIdentifier = config.projectIdentifier ?? '';
        if (config.accessTokenPresent) {
          this.accessTokenPlaceholder = '••••••••••••••••';
          this.accessToken = '';
        }

        this.saving = false;
        this.showMessage('Configuration saved successfully!', 'success');
        this.cdr.detectChanges(); // Force UI update to show "Save"

        // Notify other components that configuration was updated
        this.gitlabConfigService.notifyConfigurationUpdated();
      },
      error: (error) => {
        const duration = Date.now() - startTime;
        console.error(`[GitLab Setup] Save failed after ${duration}ms:`, error);

        this.saving = false;
        const errorMessage = error.error?.message || error.message || 'Failed to save configuration';
        this.showMessage(errorMessage, 'error');
        this.cdr.detectChanges(); // Force UI update
      },
    });
  }

  showMessage(text:string, type:'success'|'error'):void {
    this.message = text;
    this.messageType = type;
    if (type === 'success') {
      setTimeout(() => {
        this.message = '';
        this.messageType = '';
      }, 3000);
    }
  }
}

