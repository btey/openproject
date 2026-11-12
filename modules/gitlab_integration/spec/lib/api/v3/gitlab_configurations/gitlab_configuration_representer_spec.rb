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

RSpec.describe API::V3::GitlabConfigurations::GitlabConfigurationRepresenter do
  let(:project) { create(:project) }
  let(:user) { create(:user) }
  let(:configuration) do
    create(:gitlab_configuration,
           project:,
           gitlab_url: "https://gitlab.com",
           project_identifier: "test/project",
           access_token: "secret-token")
  end

  subject(:representer) { described_class.new(configuration, current_user: user) }

  describe "generation" do
    subject(:generated) { representer.to_json }

    it "includes the type" do
      expect(generated).to be_json_eql("GitlabConfiguration".to_json).at_path("_type")
    end

    it "includes the id" do
      expect(generated).to be_json_eql(configuration.id.to_json).at_path("id")
    end

    it "includes the project_id" do
      expect(generated).to be_json_eql(project.id.to_json).at_path("project_id")
    end

    it "includes the gitlab_url" do
      expect(generated).to be_json_eql("https://gitlab.com".to_json).at_path("gitlab_url")
    end

    it "includes the project_identifier" do
      expect(generated).to be_json_eql("test/project".to_json).at_path("project_identifier")
    end

    it "includes access_token_present as true when token exists" do
      expect(generated).to be_json_eql(true.to_json).at_path("access_token_present")
    end

    it "does not include the actual access_token" do
      expect(generated).not_to have_json_path("access_token")
    end

    context "when access_token is nil" do
      let(:configuration) do
        create(:gitlab_configuration,
               project:,
               gitlab_url: "https://gitlab.com",
               project_identifier: "test/project",
               access_token: nil)
      end

      it "includes access_token_present as false" do
        expect(generated).to be_json_eql(false.to_json).at_path("access_token_present")
      end
    end

    context "when fields are blank" do
      let(:configuration) do
        GitlabConfiguration.create!(project:)
      end

      it "includes null values for blank fields" do
        expect(generated).to be_json_eql(nil.to_json).at_path("gitlab_url")
        expect(generated).to be_json_eql(nil.to_json).at_path("project_identifier")
        expect(generated).to be_json_eql(false.to_json).at_path("access_token_present")
      end
    end
  end
end

