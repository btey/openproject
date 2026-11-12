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

import { Controller } from '@hotwired/stimulus';

interface GitlabConfiguration {
  id: number;
  project_id: number;
  gitlab_url: string;
  project_identifier: string;
  access_token_present: boolean;
}

export default class GitlabSetupController extends Controller {
  static targets = ['form', 'toggleButton', 'gitlabUrl', 'projectIdentifier', 'accessToken', 'saveButton', 'errorMessage'];

  declare readonly formTarget: HTMLDivElement;
  declare readonly toggleButtonTarget: HTMLButtonElement;
  declare readonly gitlabUrlTarget: HTMLInputElement;
  declare readonly projectIdentifierTarget: HTMLInputElement;
  declare readonly accessTokenTarget: HTMLInputElement;
  declare readonly saveButtonTarget: HTMLButtonElement;
  declare readonly errorMessageTarget: HTMLDivElement;
  declare readonly hasErrorMessageTarget: boolean;

  static values = {
    projectId: Number,
    apiEndpoint: String,
    canManage: Boolean,
  };

  declare projectIdValue: number;
  declare apiEndpointValue: string;
  declare canManageValue: boolean;

  connect(): void {
    this.loadConfiguration();
  }

  async loadConfiguration(): Promise<void> {
    try {
      const response = await fetch(this.apiEndpointValue, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const config: GitlabConfiguration = await response.json();
      this.populateForm(config);
    } catch (error) {
      console.error('Failed to load GitLab configuration:', error);
      this.showError('Failed to load GitLab configuration');
    }
  }

  populateForm(config: GitlabConfiguration): void {
    if (config.gitlab_url) {
      this.gitlabUrlTarget.value = config.gitlab_url;
    }
    if (config.project_identifier) {
      this.projectIdentifierTarget.value = config.project_identifier;
    }
    // Don't populate access token for security - user must re-enter if they want to change
    if (config.access_token_present) {
      this.accessTokenTarget.placeholder = '••••••••••••••••';
    }
  }

  toggleForm(event: Event): void {
    event.preventDefault();
    const isHidden = this.formTarget.style.display === 'none' || !this.formTarget.style.display;
    this.formTarget.style.display = isHidden ? 'block' : 'none';
    this.toggleButtonTarget.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
  }

  async save(event: Event): Promise<void> {
    event.preventDefault();
    this.clearError();

    const data: Record<string, string> = {
      gitlab_url: this.gitlabUrlTarget.value.trim(),
      project_identifier: this.projectIdentifierTarget.value.trim(),
    };

    // Only include access token if it's been changed (not empty and not placeholder)
    if (this.accessTokenTarget.value && this.accessTokenTarget.value !== this.accessTokenTarget.placeholder) {
      data.access_token = this.accessTokenTarget.value;
    }

    try {
      this.saveButtonTarget.disabled = true;
      this.saveButtonTarget.textContent = 'Saving...';

      const response = await fetch(this.apiEndpointValue, {
        method: 'PATCH',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'X-CSRF-Token': this.getCsrfToken(),
        },
        credentials: 'same-origin',
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      const config: GitlabConfiguration = await response.json();
      this.populateForm(config);
      this.showSuccess();
    } catch (error) {
      console.error('Failed to save GitLab configuration:', error);
      this.showError(error instanceof Error ? error.message : 'Failed to save configuration');
    } finally {
      this.saveButtonTarget.disabled = false;
      this.saveButtonTarget.textContent = 'Save';
    }
  }

  showError(message: string): void {
    if (this.hasErrorMessageTarget) {
      this.errorMessageTarget.textContent = message;
      this.errorMessageTarget.classList.remove('hidden');
      this.errorMessageTarget.classList.add('errorExplanation');
    }
  }

  clearError(): void {
    if (this.hasErrorMessageTarget) {
      this.errorMessageTarget.textContent = '';
      this.errorMessageTarget.classList.add('hidden');
      this.errorMessageTarget.classList.remove('errorExplanation');
    }
  }

  showSuccess(): void {
    if (this.hasErrorMessageTarget) {
      this.errorMessageTarget.textContent = 'Configuration saved successfully!';
      this.errorMessageTarget.classList.remove('hidden', 'errorExplanation');
      this.errorMessageTarget.classList.add('successMessage');
      setTimeout(() => {
        this.clearError();
        this.errorMessageTarget.classList.remove('successMessage');
      }, 3000);
    }
  }

  getCsrfToken(): string {
    const metaTag = document.querySelector('meta[name="csrf-token"]') as HTMLMetaElement;
    return metaTag ? metaTag.content : '';
  }
}

