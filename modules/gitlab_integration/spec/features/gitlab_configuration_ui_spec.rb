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

RSpec.describe "GitLab Configuration UI", :js, :with_cuprite do
  let(:project) { create(:project, enabled_module_names: %i[work_package_tracking gitlab]) }
  let(:work_package) { create(:work_package, project:) }
  let(:user) do
    create(:user,
           member_with_permissions: { project => permissions })
  end
  let(:permissions) { %i[view_work_packages show_gitlab_content manage_gitlab_configuration] }

  let(:work_package_page) { Pages::FullWorkPackage.new(work_package) }

  before do
    login_as(user)
  end

  context "when user has manage_gitlab_configuration permission" do
    it "shows the GitLab Setup button and allows configuration" do
      work_package_page.visit!
      work_package_page.switch_to_tab(tab: "gitlab")

      # Should show the setup button
      expect(page).to have_button("GitLab Setup")

      # Click to open the form
      click_button "GitLab Setup"

      # Form should be visible
      expect(page).to have_field("GitLab URL")
      expect(page).to have_field("Project Identifier")
      expect(page).to have_field("Access Token")
      expect(page).to have_button("Save")

      # Fill in the form
      fill_in "GitLab URL", with: "https://gitlab.example.com"
      fill_in "Project Identifier", with: "mygroup/myproject"
      fill_in "Access Token", with: "glpat-test-token-123"

      # Save the configuration
      click_button "Save"

      # Should show success message
      expect(page).to have_content("Configuration saved successfully!")

      # Verify the configuration was saved
      config = GitlabConfiguration.find_by(project:)
      expect(config).to be_present
      expect(config.gitlab_url).to eq("https://gitlab.example.com")
      expect(config.project_identifier).to eq("mygroup/myproject")
      expect(config.access_token).to eq("glpat-test-token-123")
    end

    it "allows updating existing configuration" do
      # Create existing configuration
      create(:gitlab_configuration,
             project:,
             gitlab_url: "https://old.gitlab.com",
             project_identifier: "old/project",
             access_token: "old-token")

      work_package_page.visit!
      work_package_page.switch_to_tab(tab: "gitlab")

      click_button "GitLab Setup"

      # Should show existing values
      expect(page).to have_field("GitLab URL", with: "https://old.gitlab.com")
      expect(page).to have_field("Project Identifier", with: "old/project")

      # Update the URL
      fill_in "GitLab URL", with: "https://new.gitlab.com"
      click_button "Save"

      expect(page).to have_content("Configuration saved successfully!")

      # Verify the update
      config = GitlabConfiguration.find_by(project:)
      expect(config.gitlab_url).to eq("https://new.gitlab.com")
      expect(config.project_identifier).to eq("old/project")
      expect(config.access_token).to eq("old-token")
    end
  end

  context "when user does not have manage_gitlab_configuration permission" do
    let(:permissions) { %i[view_work_packages show_gitlab_content] }

    it "does not show the GitLab Setup button" do
      work_package_page.visit!
      work_package_page.switch_to_tab(tab: "gitlab")

      expect(page).not_to have_button("GitLab Setup")
    end
  end

  context "when user does not have show_gitlab_content permission" do
    let(:permissions) { %i[view_work_packages] }

    it "does not show the GitLab tab" do
      work_package_page.visit!

      expect(page).not_to have_content("GITLAB")
    end
  end
end

