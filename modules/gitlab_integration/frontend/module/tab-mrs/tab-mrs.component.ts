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

import { ChangeDetectorRef, Component, Input, OnInit, OnChanges, OnDestroy, SimpleChanges, inject, ChangeDetectionStrategy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { WorkPackageResource } from "core-app/features/hal/resources/work-package-resource";
import { HalResourceService } from "core-app/features/hal/services/hal-resource.service";
import { CollectionResource } from "core-app/features/hal/resources/collection-resource";
import { I18nService } from "core-app/core/i18n/i18n.service";
import {IGitlabMergeRequestResource} from "core-app/features/plugins/linked/openproject-gitlab_integration/typings";
import {ApiV3Service} from "core-app/core/apiv3/api-v3.service";

@Component({
  selector: 'tab-mrs',
  templateUrl: './tab-mrs.template.html',
  host: { class: 'op-mrs' },
  changeDetection: ChangeDetectionStrategy.Eager,
  standalone: false,
})
export class TabMrsComponent implements OnInit, OnChanges, OnDestroy {
  readonly I18n = inject(I18nService);
  readonly apiV3Service = inject(ApiV3Service);
  readonly halResourceService = inject(HalResourceService);
  readonly changeDetector = inject(ChangeDetectorRef);
  readonly httpClient = inject(HttpClient);

  @Input() public workPackage:WorkPackageResource;

  public mergeRequests:IGitlabMergeRequestResource[] = [];

  private destroy$ = new Subject<void>();
  private requestCounter = 0;  // Track request sequence to ignore stale responses

  ngOnInit(): void {
    this.loadMergeRequests();
  }

  ngOnChanges(changes: SimpleChanges): void {
    // Reload merge requests when work package changes
    if (changes['workPackage']) {
      const change = changes['workPackage'];
      console.log('ngOnChanges triggered:', {
        firstChange: change.firstChange,
        previousValue: change.previousValue?.displayId,
        currentValue: change.currentValue?.displayId
      });

      if (!change.firstChange) {
        console.log('Work package changed from', change.previousValue?.displayId, 'to', change.currentValue?.displayId);
        // Cancel pending requests and load fresh data
        this.destroy$.next();
        this.loadMergeRequests();
      }
    }
  }

  ngOnDestroy(): void {
    // Cancel any pending requests when component is destroyed
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadMergeRequests(): void {
    // Increment and capture request ID to track this specific request
    const requestId = ++this.requestCounter;

    // Capture work package ID at request start
    const currentWorkPackageId = this.workPackage.displayId as string;
    const basePath = this.apiV3Service.work_packages.id(currentWorkPackageId).path;
    const mergeRequestsPath = `${basePath}/gitlab_merge_requests`;

    console.log(`[Request #${requestId}] Loading MRs for WP ${currentWorkPackageId} from:`, mergeRequestsPath);

    // Use HttpClient directly to bypass HAL resource caching
    // Add headers to prevent browser HTTP caching
    this.httpClient
      .get<any>(mergeRequestsPath, {
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      })
      .pipe(takeUntil(this.destroy$))
      .subscribe((value) => {
        // CRITICAL: Check if this is still the most recent request
        if (requestId !== this.requestCounter) {
          console.warn(`[Request #${requestId}] DISCARDED - newer request #${this.requestCounter} superseded this`);
          return;
        }

        // Double-check work package hasn't changed
        if (this.workPackage.displayId !== currentWorkPackageId) {
          console.warn(`[Request #${requestId}] DISCARDED - WP changed from ${currentWorkPackageId} to ${this.workPackage.displayId}`);
          return;
        }

        this.mergeRequests = value._embedded?.elements || [];
        console.log(`[Request #${requestId}] ✅ APPLIED - Loaded ${this.mergeRequests.length} MRs for WP ${currentWorkPackageId}`);
        this.mergeRequests.forEach((mr) => {
          console.log('  MR #' + mr.id, 'delete link:', (mr as any)._links?.delete?.href);
        });
        this.changeDetector.detectChanges();
      });
  }

  public getEmptyText() {
    return this.I18n.t('js.gitlab_integration.tab_mrs.empty',{ wp_id: this.workPackage.displayId });
  }

  public onMergeRequestDeleted(mergeRequest:IGitlabMergeRequestResource):void {
    this.mergeRequests = this.mergeRequests.filter(mr => mr.id !== mergeRequest.id);
    this.changeDetector.detectChanges();
  }
}
