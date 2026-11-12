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
      class CreateMergeRequest
        def initialize(work_package:, user:, private_link: false)
          @work_package = work_package
          @user = user
          @private_link = private_link
        end

        def call
          return ServiceResult.failure(message: "GitLab not configured for this project") unless gitlab_config&.configured?

          # First, create the branch in GitLab
          branch_response = create_branch_on_gitlab

          # Handle branch already exists error (HTTP 400 with specific message)
          if branch_response.code.to_i == 400
            body = JSON.parse(branch_response.body) rescue { "message" => branch_response.message }
            error_message = body.dig("message") || body.dig("error") || ""

            # Check if the error is because branch already exists
            if error_message.include?("already exists") || error_message.include?("Branch already exists")
              Rails.logger.info "Branch #{branch_name} already exists, checking if it can be reused"

              # Check if there's an open MR with this branch
              existing_mr = check_existing_merge_request

              if existing_mr
                # If there's already an open MR with this branch, return that
                return ServiceResult.success(result: existing_mr, reused: true)
              else
                # Branch exists but no open MR - try to delete the branch and recreate
                delete_response = delete_branch_on_gitlab
                if delete_response.is_a?(Net::HTTPSuccess) || delete_response.code.to_i == 204
                  # Successfully deleted, try creating again
                  branch_response = create_branch_on_gitlab
                else
                  # Can't delete branch, append timestamp to make it unique
                  @branch_name_suffix = Time.now.to_i
                  branch_response = create_branch_on_gitlab
                end
              end
            end
          end

          unless branch_response.is_a?(Net::HTTPSuccess) || branch_response.is_a?(Net::HTTPCreated)
            body = JSON.parse(branch_response.body) rescue { "message" => branch_response.message }
            error_message = body.dig("message") || body.dig("error") || branch_response.message
            return ServiceResult.failure(message: "Failed to create branch: #{error_message}")
          end

          # Then, create the merge request
          response = create_merge_request_on_gitlab

          if response.is_a?(Net::HTTPSuccess)
            body = JSON.parse(response.body)
            ServiceResult.success(result: body)
          else
            body = JSON.parse(response.body) rescue { "message" => response.message }
            error_message = body.dig("message") || body.dig("error") || response.message
            ServiceResult.failure(message: "Failed to create merge request: #{error_message}")
          end
        rescue StandardError => e
          Rails.logger.error "Error creating merge request: #{e.message}"
          Rails.logger.error e.backtrace.join("\n")
          ServiceResult.failure(message: "Error creating merge request: #{e.message}")
        end

        private

        attr_reader :work_package, :user, :private_link

        def gitlab_config
          @gitlab_config ||= GitlabConfiguration.for_project(work_package.project)
        end

        def create_branch_on_gitlab
          target_branch = fetch_gitlab_project_default_branch
          uri = URI("#{gitlab_config.gitlab_url}/api/v4/projects/#{CGI.escape(gitlab_config.project_identifier)}/repository/branches")

          http = Net::HTTP.new(uri.host, uri.port)
          http.use_ssl = uri.scheme == "https"

          request = Net::HTTP::Post.new(uri)
          request["Content-Type"] = "application/json"
          request["PRIVATE-TOKEN"] = gitlab_config.access_token
          request.body = {
            branch: branch_name,
            ref: target_branch
          }.to_json

          http.request(request)
        end

        def delete_branch_on_gitlab
          uri = URI("#{gitlab_config.gitlab_url}/api/v4/projects/#{CGI.escape(gitlab_config.project_identifier)}/repository/branches/#{CGI.escape(branch_name)}")

          http = Net::HTTP.new(uri.host, uri.port)
          http.use_ssl = uri.scheme == "https"

          request = Net::HTTP::Delete.new(uri)
          request["PRIVATE-TOKEN"] = gitlab_config.access_token

          http.request(request)
        rescue StandardError => e
          Rails.logger.error "Error deleting branch: #{e.message}"
          # Return a failed response object
          Net::HTTPBadRequest.new("1.1", "400", "Failed to delete branch")
        end

        def check_existing_merge_request
          # Check if there's an open MR with the same source branch
          uri = URI("#{gitlab_config.gitlab_url}/api/v4/projects/#{CGI.escape(gitlab_config.project_identifier)}/merge_requests")
          uri.query = URI.encode_www_form({
            state: "opened",
            source_branch: branch_name
          })

          http = Net::HTTP.new(uri.host, uri.port)
          http.use_ssl = uri.scheme == "https"

          request = Net::HTTP::Get.new(uri)
          request["PRIVATE-TOKEN"] = gitlab_config.access_token

          response = http.request(request)

          if response.is_a?(Net::HTTPSuccess)
            merge_requests = JSON.parse(response.body)
            merge_requests.first if merge_requests.any?
          else
            nil
          end
        rescue StandardError => e
          Rails.logger.error "Error checking existing merge request: #{e.message}"
          nil
        end

        def create_merge_request_on_gitlab
          uri = URI("#{gitlab_config.gitlab_url}/api/v4/projects/#{CGI.escape(gitlab_config.project_identifier)}/merge_requests")

          http = Net::HTTP.new(uri.host, uri.port)
          http.use_ssl = uri.scheme == "https"

          request = Net::HTTP::Post.new(uri)
          request["Content-Type"] = "application/json"
          request["PRIVATE-TOKEN"] = gitlab_config.access_token
          request.body = merge_request_payload.to_json

          http.request(request)
        end

        def fetch_gitlab_project_default_branch
          uri = URI("#{gitlab_config.gitlab_url}/api/v4/projects/#{CGI.escape(gitlab_config.project_identifier)}")

          http = Net::HTTP.new(uri.host, uri.port)
          http.use_ssl = uri.scheme == "https"

          request = Net::HTTP::Get.new(uri)
          request["PRIVATE-TOKEN"] = gitlab_config.access_token

          response = http.request(request)

          if response.is_a?(Net::HTTPSuccess)
            project_data = JSON.parse(response.body)
            project_data["default_branch"] || "main"
          else
            Rails.logger.warn "Failed to fetch GitLab project info, falling back to 'main' branch"
            "main"
          end
        rescue StandardError => e
          Rails.logger.error "Error fetching GitLab default branch: #{e.message}"
          "main" # Fallback to 'main' if fetch fails
        end

        def merge_request_payload
          {
            source_branch: branch_name,
            target_branch: fetch_gitlab_project_default_branch,
            title: merge_request_title,
            description: merge_request_description,
            remove_source_branch: true
          }
        end

        def branch_prefix
          work_package.type.name.downcase.gsub(/\s+/, "-")
        end

        def branch_name
          base_name = "#{branch_prefix}/op-#{work_package.id}-#{work_package.subject.parameterize[0..40]}"
          @branch_name_suffix ? "#{base_name}-#{@branch_name_suffix}" : base_name
        end

        def merge_request_title
          "#{work_package.subject} — #{prefix}##{work_package.id}"
        end

        def merge_request_description
          <<~DESC
            This merge request is related to OpenProject work package #{prefix}##{work_package.id}

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

