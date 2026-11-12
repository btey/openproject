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

require "roar/decorator"
require "roar/json/hal"

module API
  module V3
    module GitlabIssues
      class GitlabIssueRepresenter < ::API::Decorators::Single
        include API::Caching::CachedRepresenter
        include API::Decorators::DateProperty
        include API::Decorators::FormattableProperty
        include API::Decorators::LinkedResource

        def initialize(model, current_user:, work_package_id: nil, **_opts)
          # We force `embed_links` so that github_user and github_check_runs
          # are embedded and we can avoid having separate endpoints.
          super(model, current_user:, embed_links: true)
          @work_package_id = work_package_id
        end

        # Caching disabled because the delete link varies per work_package context
        # The same issue can be linked to multiple WPs and needs different delete URLs
        # cached_representer key_parts: %i[gitlab_user],
        #                    key_expander: ->(*) { @work_package_id }

        property :id

        property :number

        property :gitlab_html_url, as: :htmlUrl

        property :state,
                 render_nil: true

        property :repository,
                 render_nil: true

        date_time_property :gitlab_updated_at,
                           render_nil: true,
                           setter: ->(*) {}

        property :title,
                 render_nil: true

        formattable_property :body,
                             render_nil: true

        property :labels

        associated_resource :gitlab_user,
                            representer: ::API::V3::GitlabIssues::GitlabUserRepresenter,
                            link_title_attribute: :gitlab_name

        property :gitlab_author_name,
                 as: :gitlabAuthorName,
                 render_nil: true

        date_time_property :created_at

        date_time_property :updated_at

        link :delete do
          next unless embed_links
          next unless @work_package_id
          next unless delete_allowed?

          {
            href: api_v3_paths.work_package(@work_package_id) + "/gitlab_issues/#{represented.id}",
            method: :delete
          }
        end

        def _type
          "GitlabIssue"
        end

        def delete_allowed?
          work_package = WorkPackage.find_by(id: @work_package_id)
          return false unless work_package

          current_user.allowed_in_work_package?(:delete_gitlab_links, work_package)
        end

        self.to_eager_load = %i[gitlab_user]
      end
    end
  end
end
