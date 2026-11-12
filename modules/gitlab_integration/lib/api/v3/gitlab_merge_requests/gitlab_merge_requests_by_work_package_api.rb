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
    module GitlabMergeRequests
      class GitlabMergeRequestsByWorkPackageAPI < ::API::OpenProjectAPI
        after_validation do
          authorize_in_work_package(:show_gitlab_content, work_package: @work_package)
          @gitlab_merge_requests = @work_package.gitlab_merge_requests
        end

        resources :gitlab_merge_requests do
          get do
            Rails.logger.info "=" * 80
            Rails.logger.info "GET MRs REQUEST"
            Rails.logger.info "@work_package.id: #{@work_package.id}"
            Rails.logger.info "MR count: #{@gitlab_merge_requests.count}"
            @gitlab_merge_requests.each do |mr|
              Rails.logger.info "  - MR ##{mr.id} (GitLab ##{mr.number})"
            end
            Rails.logger.info "=" * 80

            # Set response headers to prevent caching
            # This ensures each work package gets fresh data with correct delete links
            header 'Cache-Control', 'no-cache, no-store, must-revalidate, private'
            header 'Pragma', 'no-cache'
            header 'Expires', '0'

            path = api_v3_paths.gitlab_merge_requests_by_work_package(@work_package.id)
            GitlabMergeRequestCollectionRepresenter.new(@gitlab_merge_requests,
                                                        @gitlab_merge_requests.count,
                                                        self_link: path,
                                                        current_user:,
                                                        work_package_id: @work_package.id)
          end

          namespace ":merge_request_id" do
            params do
              requires :merge_request_id, desc: "GitLab Merge Request ID", type: Integer
            end

            delete do
              Rails.logger.info "=" * 80
              Rails.logger.info "DELETE MR REQUEST RECEIVED"
              Rails.logger.info "Route param :id (from URL): #{params[:id]}"
              Rails.logger.info "@work_package.id: #{@work_package.id}"
              Rails.logger.info "merge_request_id param: #{params[:merge_request_id]}"
              Rails.logger.info "Full request path: #{request.path}"
              Rails.logger.info "=" * 80

              # Check permission before allowing deletion
              authorize_in_work_package(:delete_gitlab_links, work_package: @work_package)

              merge_request = GitlabMergeRequest.find_by(id: params[:merge_request_id])

              if merge_request.nil?
                Rails.logger.error "DELETE MR - Merge request not found: #{params[:merge_request_id]}"
                raise API::Errors::NotFound.new
              end

              # Delete directly from the join table to remove only the link, not the MR itself
              sql = <<-SQL
                DELETE FROM gitlab_merge_requests_work_packages
                WHERE work_package_id = :work_package_id
                  AND gitlab_merge_request_id = :merge_request_id
              SQL

              result = ActiveRecord::Base.connection.execute(
                ActiveRecord::Base.sanitize_sql([
                  sql,
                  { work_package_id: @work_package.id, merge_request_id: merge_request.id }
                ])
              )

              deleted_count = result.cmd_tuples

              if deleted_count.zero?
                Rails.logger.error "DELETE MR - Link not found between WP #{@work_package.id} and MR #{merge_request.id}"
                raise API::Errors::NotFound.new
              end

              Rails.logger.info "DELETE MR - Successfully deleted link (#{deleted_count} record from join table)"
              Rails.logger.info "=" * 80

              status 204
            end
          end
        end
      end
    end
  end
end
