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

module API
  module V3
    module GitlabConfigurations
      class GitlabConfigurationByProjectAPI < ::API::OpenProjectAPI
        helpers do
          def configuration_params
            {
              gitlab_url: params[:gitlab_url],
              project_identifier: params[:project_identifier],
              access_token: params[:access_token]
            }.compact
          end
        end

        resources :gitlab_configuration do
          # GET /api/v3/projects/:project_id/gitlab_configuration
          get do
            authorize_in_project(:show_gitlab_content, project: @project)

            configuration = GitlabConfiguration.find_or_create_for_project(@project)

            GitlabConfigurationRepresenter.new(configuration, current_user:)
          end

          # PATCH /api/v3/projects/:project_id/gitlab_configuration
          patch do
            authorize_in_project(:manage_gitlab_configuration, project: @project)

            configuration = GitlabConfiguration.find_or_create_for_project(@project)

            if configuration.update(configuration_params)
              GitlabConfigurationRepresenter.new(configuration, current_user:)
            else
              fail ::API::Errors::Validation.new(configuration)
            end
          end
        end
      end
    end
  end
end

