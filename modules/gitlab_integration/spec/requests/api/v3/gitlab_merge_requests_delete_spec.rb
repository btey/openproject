# frozen_string_literal: true

#-- copyright
# OpenProject is an open source project management software.
# Copyright (C) 2023 Ben Tey
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License version 3.
#
# OpenProject is a fork of ChiliProject, which is a fork of Redmine. The copyright follows:
# Copyright (C) 2006-2013 Jean-Philippe Lang
# Copyright (C) 2010-2013 the ChiliProject Team
# Copyright (C) the OpenProject GmbH
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# See docs/COPYRIGHT.rdoc for more details.
#++

require "spec_helper"
require_module_spec_helper

RSpec.describe "API v3 GitLab Merge Requests Delete", content_type: :json do
  include API::V3::Utilities::PathHelper

  let(:project) { create(:project, enabled_module_names: %i[gitlab work_package_tracking]) }
  let(:work_package) { create(:work_package, project:) }
  let(:gitlab_merge_request) { create(:gitlab_merge_request) }
  let(:user) do
    create(:user,
           member_with_permissions: { project => permissions })
  end
  let(:permissions) { %i[view_work_packages show_gitlab_content delete_gitlab_links] }

  before do
    # Create the link between work package and merge request
    work_package.gitlab_merge_requests << gitlab_merge_request
    login_as(user)
  end

  describe "DELETE /api/v3/work_packages/:work_package_id/gitlab_merge_requests/:merge_request_id" do
    let(:path) { "/api/v3/work_packages/#{work_package.id}/gitlab_merge_requests/#{gitlab_merge_request.id}" }

    context "with delete_gitlab_links permission" do
      it "deletes the link between work package and merge request" do
        expect { delete path }
          .to change { work_package.reload.gitlab_merge_requests.count }.by(-1)

        expect(response).to have_http_status(:no_content)
      end

      it "does not delete the merge request itself" do
        expect { delete path }
          .not_to change(GitlabMergeRequest, :count)
      end
    end

    context "without delete_gitlab_links permission" do
      let(:permissions) { %i[view_work_packages show_gitlab_content] }

      it "returns 403 Forbidden" do
        delete path

        expect(response).to have_http_status(:forbidden)
      end

      it "does not delete the link" do
        expect { delete path }
          .not_to change { work_package.reload.gitlab_merge_requests.count }
      end
    end

    context "without show_gitlab_content permission" do
      let(:permissions) { %i[view_work_packages] }

      it "returns 403 Forbidden" do
        delete path

        expect(response).to have_http_status(:forbidden)
      end
    end

    context "when merge request does not exist" do
      let(:path) { "/api/v3/work_packages/#{work_package.id}/gitlab_merge_requests/99999" }

      it "returns 404 Not Found" do
        delete path

        expect(response).to have_http_status(:not_found)
      end
    end

    context "when link does not exist" do
      let(:other_merge_request) { create(:gitlab_merge_request) }
      let(:path) { "/api/v3/work_packages/#{work_package.id}/gitlab_merge_requests/#{other_merge_request.id}" }

      it "returns 404 Not Found" do
        delete path

        expect(response).to have_http_status(:not_found)
      end
    end
  end
end

