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
      class GitlabMergeRequestCollectionRepresenter < ::API::Decorators::Collection
        self.to_eager_load = ::API::V3::GitlabMergeRequests::GitlabMergeRequestRepresenter.to_eager_load

        attr_accessor :work_package_id

        def initialize(models, total, self_link:, current_user:, groups: nil, work_package_id: nil)
          @work_package_id = work_package_id
          Rails.logger.info "MR Collection Representer initialized: work_package_id: #{work_package_id.inspect}, MR count: #{models.count}"
          super(models, total, self_link:, current_user:, groups:)
        end

        collection :elements,
                   getter: ->(*) {
                     Rails.logger.info "MR Collection: Creating #{represented.count} elements with work_package_id: #{@work_package_id.inspect}"
                     represented.map do |model|
                       element_decorator.create(model, current_user:, work_package_id: @work_package_id)
                     end
                   },
                   exec_context: :decorator,
                   embedded: true
      end
    end
  end
end
