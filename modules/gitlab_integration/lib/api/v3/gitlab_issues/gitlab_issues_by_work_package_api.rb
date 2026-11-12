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
    module GitlabIssues
      class GitlabIssuesByWorkPackageAPI < ::API::OpenProjectAPI
        after_validation do
          authorize_in_work_package(:show_gitlab_content, work_package: @work_package)
          @gitlab_issues = @work_package.gitlab_issues
        end

        resources :gitlab_issues do
          get do
            # Set response headers to prevent caching
            # This ensures each work package gets fresh data with correct delete links
            header 'Cache-Control', 'no-cache, no-store, must-revalidate, private'
            header 'Pragma', 'no-cache'
            header 'Expires', '0'

            path = api_v3_paths.gitlab_issues_by_work_package(@work_package.id)
            GitlabIssueCollectionRepresenter.new(@gitlab_issues,
                                                 @gitlab_issues.count,
                                                 self_link: path,
                                                 current_user:,
                                                 work_package_id: @work_package.id)
          end

          namespace ":issue_id" do
            params do
              requires :issue_id, desc: "GitLab Issue ID", type: Integer
            end

            delete do
              Rails.logger.info "DELETE Issue - work_package_id: #{@work_package.id}, issue_id: #{params[:issue_id]}"

              # Check permission before allowing deletion
              authorize_in_work_package(:delete_gitlab_links, work_package: @work_package)

              issue = GitlabIssue.find_by(id: params[:issue_id])

              if issue.nil?
                Rails.logger.error "DELETE Issue - Issue not found: #{params[:issue_id]}"
                raise API::Errors::NotFound.new
              end

              # Delete directly from the join table to remove only the link, not the issue itself
              sql = <<-SQL
                DELETE FROM gitlab_issues_work_packages
                WHERE work_package_id = :work_package_id
                  AND gitlab_issue_id = :issue_id
              SQL

              result = ActiveRecord::Base.connection.execute(
                ActiveRecord::Base.sanitize_sql([
                  sql,
                  { work_package_id: @work_package.id, issue_id: issue.id }
                ])
              )

              deleted_count = result.cmd_tuples

              if deleted_count.zero?
                Rails.logger.error "DELETE Issue - Link not found between WP #{@work_package.id} and Issue #{issue.id}"
                raise API::Errors::NotFound.new
              end

              Rails.logger.info "DELETE Issue - Successfully deleted link (#{deleted_count} record from join table)"

              status 204
            end
          end
        end
      end
    end
  end
end
