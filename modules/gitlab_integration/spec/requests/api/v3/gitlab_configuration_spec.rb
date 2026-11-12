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

RSpec.describe "API v3 GitLab Configuration", :webmock, content_type: :json do
  include API::V3::Utilities::PathHelper

  let(:project) { create(:project, enabled_module_names: %i[gitlab]) }
  let(:user) do
    create(:user,
           member_with_permissions: { project => permissions })
  end
  let(:permissions) { %i[show_gitlab_content manage_gitlab_configuration] }

  before do
    login_as(user)
  end

  describe "GET /api/v3/projects/:project_id/gitlab_configuration" do
    let(:path) { "/api/v3/projects/#{project.id}/gitlab_configuration" }

    context "when configuration does not exist" do
      it "auto-creates and returns an empty configuration" do
        get path

        expect(response).to have_http_status(:ok)
        expect(response.body).to be_json_eql("GitlabConfiguration".to_json).at_path("_type")
        expect(response.body).to be_json_eql(project.id.to_json).at_path("project_id")
        expect(response.body).to be_json_eql(nil.to_json).at_path("gitlab_url")
        expect(response.body).to be_json_eql(nil.to_json).at_path("project_identifier")
        expect(response.body).to be_json_eql(false.to_json).at_path("access_token_present")
      end
    end

    context "when configuration exists" do
      let!(:configuration) do
        create(:gitlab_configuration,
               project:,
               gitlab_url: "https://gitlab.example.com",
               project_identifier: "test/project",
               access_token: "secret-token")
      end

      it "returns the existing configuration" do
        get path

        expect(response).to have_http_status(:ok)
        expect(response.body).to be_json_eql("GitlabConfiguration".to_json).at_path("_type")
        expect(response.body).to be_json_eql("https://gitlab.example.com".to_json).at_path("gitlab_url")
        expect(response.body).to be_json_eql("test/project".to_json).at_path("project_identifier")
        expect(response.body).to be_json_eql(true.to_json).at_path("access_token_present")
      end

      it "does not expose the access token" do
        get path

        expect(response.body).not_to have_json_path("access_token")
      end
    end

    context "without manage permission" do
      let(:permissions) { %i[show_gitlab_content] }

      it "allows viewing the configuration" do
        get path

        expect(response).to have_http_status(:ok)
      end
    end

    context "without show_gitlab_content permission" do
      let(:permissions) { [] }

      it "returns forbidden" do
        get path

        expect(response).to have_http_status(:forbidden)
      end
    end
  end

  describe "PATCH /api/v3/projects/:project_id/gitlab_configuration" do
    let(:path) { "/api/v3/projects/#{project.id}/gitlab_configuration" }
    let(:params) do
      {
        gitlab_url: "https://gitlab.com",
        project_identifier: "mygroup/myproject",
        access_token: "new-token"
      }
    end

    context "when configuration does not exist" do
      it "creates and updates the configuration" do
        expect do
          patch path, params: params.to_json
        end.to change(GitlabConfiguration, :count).by(1)

        expect(response).to have_http_status(:ok)
        expect(response.body).to be_json_eql("https://gitlab.com".to_json).at_path("gitlab_url")
        expect(response.body).to be_json_eql("mygroup/myproject".to_json).at_path("project_identifier")
        expect(response.body).to be_json_eql(true.to_json).at_path("access_token_present")

        config = GitlabConfiguration.find_by(project:)
        expect(config.access_token).to eq("new-token")
      end
    end

    context "when configuration exists" do
      let!(:configuration) do
        create(:gitlab_configuration,
               project:,
               gitlab_url: "https://old.gitlab.com",
               project_identifier: "old/project",
               access_token: "old-token")
      end

      it "updates the configuration" do
        expect do
          patch path, params: params.to_json
        end.not_to change(GitlabConfiguration, :count)

        expect(response).to have_http_status(:ok)
        expect(response.body).to be_json_eql("https://gitlab.com".to_json).at_path("gitlab_url")

        configuration.reload
        expect(configuration.gitlab_url).to eq("https://gitlab.com")
        expect(configuration.project_identifier).to eq("mygroup/myproject")
        expect(configuration.access_token).to eq("new-token")
      end

      it "allows partial updates" do
        patch path, params: { gitlab_url: "https://new.gitlab.com" }.to_json

        expect(response).to have_http_status(:ok)

        configuration.reload
        expect(configuration.gitlab_url).to eq("https://new.gitlab.com")
        expect(configuration.project_identifier).to eq("old/project")
        expect(configuration.access_token).to eq("old-token")
      end
    end

    context "without manage_gitlab_configuration permission" do
      let(:permissions) { %i[show_gitlab_content] }

      it "returns forbidden" do
        patch path, params: params.to_json

        expect(response).to have_http_status(:forbidden)
      end
    end

    context "with invalid data" do
      let(:params) do
        {
          gitlab_url: "not-a-valid-url",
          project_identifier: "test/project"
        }
      end

      it "returns validation errors" do
        patch path, params: params.to_json

        expect(response).to have_http_status(:unprocessable_entity)
      end
    end
  end
end

