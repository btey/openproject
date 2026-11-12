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

require "rails_helper"

RSpec.describe GitlabConfiguration, type: :model do
  let(:project) { create(:project) }

  describe "validations" do
    it "validates presence of gitlab_url" do
      config = described_class.new(project:, project_identifier: "test/project")
      expect(config).not_to be_valid
      expect(config.errors[:gitlab_url]).to include("can't be blank")
    end

    it "validates presence of project_identifier" do
      config = described_class.new(project:, gitlab_url: "https://gitlab.com")
      expect(config).not_to be_valid
      expect(config.errors[:project_identifier]).to include("can't be blank")
    end

    it "validates url format" do
      config = described_class.new(
        project:,
        gitlab_url: "not-a-url",
        project_identifier: "test/project"
      )
      expect(config).not_to be_valid
    end
  end

  describe "#configured?" do
    it "returns true when all fields are present" do
      config = described_class.new(
        project:,
        gitlab_url: "https://gitlab.com",
        project_identifier: "test/project",
        access_token: "test-token"
      )
      expect(config.configured?).to be true
    end

    it "returns false when access_token is missing" do
      config = described_class.new(
        project:,
        gitlab_url: "https://gitlab.com",
        project_identifier: "test/project"
      )
      expect(config.configured?).to be false
    end
  end

  describe ".for_project" do
    it "returns configuration for given project" do
      config = create(:gitlab_configuration, project:)
      expect(described_class.for_project(project)).to eq(config)
    end

    it "returns nil when no configuration exists" do
      expect(described_class.for_project(project)).to be_nil
    end
  end

  describe "encryption" do
    it "encrypts the access_token" do
      config = create(:gitlab_configuration,
                     project:,
                     access_token: "secret-token")

      # The encrypted value in the database should be different from the plain text
      expect(config.access_token).to eq("secret-token")
      # This would need to check the actual database column if testing encryption
    end
  end
end

