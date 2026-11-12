# frozen_string_literal: true

require "net/http"
require "uri"
require "json"
require "erb"

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

module OpenProject
  module GitlabIntegration
    module Services
      class CreateIssue
        def initialize(work_package:, user:, private_link: false)
          @work_package = work_package
          @user = user
          @private_link = private_link
        end

        def call
          return ServiceResult.failure(message: "GitLab not configured for this project") unless gitlab_config&.configured?

          response = create_issue_on_gitlab

          if response.is_a?(Net::HTTPSuccess)
            body = JSON.parse(response.body)
            ServiceResult.success(result: body)
          else
            body = JSON.parse(response.body) rescue { "message" => response.message }
            error_message = body.dig("message") || body.dig("error") || response.message
            ServiceResult.failure(message: "Failed to create issue: #{error_message}")
          end
        rescue StandardError => e
          Rails.logger.error "Error creating issue: #{e.message}"
          Rails.logger.error e.backtrace.join("\n")
          ServiceResult.failure(message: "Error creating issue: #{e.message}")
        end

        private

        attr_reader :work_package, :user, :private_link

        def gitlab_config
          @gitlab_config ||= GitlabConfiguration.for_project(work_package.project)
        end

        def create_issue_on_gitlab
          uri = URI("#{gitlab_config.gitlab_url}/api/v4/projects/#{CGI.escape(gitlab_config.project_identifier)}/issues")

          http = Net::HTTP.new(uri.host, uri.port)
          http.use_ssl = uri.scheme == "https"

          request = Net::HTTP::Post.new(uri)
          request["Content-Type"] = "application/json"
          request["PRIVATE-TOKEN"] = gitlab_config.access_token
          request.body = issue_payload.to_json

          http.request(request)
        end

        def issue_payload
          {
            title: issue_title,
            description: issue_description
          }
        end

        def issue_title
          "#{work_package.subject} — #{prefix}##{work_package.id}"
        end

        def issue_description
          <<~DESC
            This issue is related to OpenProject work package #{prefix}##{work_package.id}

            **Work Package:** #{work_package.subject}

            ---

            #{work_package.description}
          DESC
        end

        def prefix
          private_link ? "PP" : "OP"
        end
      end
    end
  end
end

