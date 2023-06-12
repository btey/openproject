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
//++

import { Injectable } from '@angular/core';
import { WorkPackageResource } from 'core-app/features/hal/resources/work-package-resource';
import { IGitlabMergeRequest } from 'core-app/features/plugins/linked/openproject-gitlab_integration/state/gitlab-merge-request.model';
import { GitlabMergeRequestsStore } from 'core-app/features/plugins/linked/openproject-gitlab_integration/state/gitlab-merge-request.store';
import { ID } from '@datorama/akita';
import { ResourceStoreService, ResourceStore } from 'core-app/core/state/resource-store.service';
import { Observable } from 'rxjs';

@Injectable()
export class GitlabMergeRequestResourceService extends ResourceStoreService<IGitlabMergeRequest> {
  ofWorkPackage(workPackage:WorkPackageResource):Observable<IGitlabMergeRequest[]> {
    const path = this.workPackageMergeRequestsPath(workPackage.id as string);
    return this.requireCollection(path);
  }

  requireSingle(id:ID):Observable<IGitlabMergeRequest> {
    return this.requireEntity(this.entityPath(id));
  }

  protected basePath():string {
    return this.apiV3Service.gitlab_merge_requests.path;
  }

  protected entityPath(id:ID):string {
    return this.apiV3Service.gitlab_merge_requests.id(id).path;
  }

  protected workPackageMergeRequestsPath(id:ID):string {
    return this.apiV3Service.work_packages.id(id).gitlab_merge_requests.path;
  }

  protected createStore():ResourceStore<IGitlabMergeRequest> {
    return new GitlabMergeRequestsStore();
  }
}