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

namespace :gitlab_integration do
  desc "Configure GitLab integration for a project"
  task :configure, [:project_identifier, :gitlab_url, :gitlab_project_identifier, :access_token] => :environment do |_t, args|
    unless args[:project_identifier] && args[:gitlab_url] && args[:gitlab_project_identifier] && args[:access_token]
      puts "Usage: rake gitlab_integration:configure[project_identifier,gitlab_url,gitlab_project_identifier,access_token]"
      puts ""
      puts "Example:"
      puts "  rake gitlab_integration:configure[demo-project,https://gitlab.com,group/project,glpat-xxxxx]"
      puts ""
      puts "Arguments:"
      puts "  project_identifier: OpenProject project identifier (STRING, e.g., 'demo-project', NOT the numeric ID)"
      puts "  gitlab_url: GitLab instance URL (e.g., https://gitlab.com)"
      puts "  gitlab_project_identifier: GitLab project path or ID (e.g., group/project or 12345)"
      puts "  access_token: GitLab access token with 'api' scope"
      puts ""
      puts "To find your project identifier, check the project URL or run:"
      puts "  bundle exec rails runner \"Project.all.each { |p| puts '  ' + p.identifier + ' => ' + p.name }\""
      exit 1
    end

    project = Project.find_by(identifier: args[:project_identifier])

    unless project
      puts "Error: Project with identifier '#{args[:project_identifier]}' not found"
      puts ""
      puts "Available projects:"
      Project.all.each { |p| puts "  #{p.identifier} => #{p.name}" }
      exit 1
    end

    config = GitlabConfiguration.find_or_initialize_by(project:)
    config.gitlab_url = args[:gitlab_url]
    config.project_identifier = args[:gitlab_project_identifier]
    config.access_token = args[:access_token]

    if config.save
      puts "✓ GitLab integration configured successfully for project '#{project.name}'"
      puts ""
      puts "Configuration:"
      puts "  GitLab URL: #{config.gitlab_url}"
      puts "  GitLab Project: #{config.project_identifier}"
      puts "  Access Token: [ENCRYPTED]"
    else
      puts "Error: Failed to save configuration"
      puts config.errors.full_messages.join("\n")
      exit 1
    end
  end

  desc "Show GitLab configuration for a project"
  task :show, [:project_identifier] => :environment do |_t, args|
    unless args[:project_identifier]
      puts "Usage: rake gitlab_integration:show[project_identifier]"
      exit 1
    end

    project = Project.find_by(identifier: args[:project_identifier])

    unless project
      puts "Error: Project '#{args[:project_identifier]}' not found"
      exit 1
    end

    config = GitlabConfiguration.find_by(project:)

    if config
      puts "GitLab Configuration for '#{project.name}':"
      puts "  GitLab URL: #{config.gitlab_url}"
      puts "  GitLab Project: #{config.project_identifier}"
      puts "  Access Token: #{config.access_token.present? ? '[CONFIGURED]' : '[NOT SET]'}"
      puts "  Status: #{config.configured? ? '✓ Configured' : '✗ Incomplete'}"
    else
      puts "No GitLab configuration found for project '#{project.name}'"
    end
  end

  desc "Remove GitLab configuration for a project"
  task :remove, [:project_identifier] => :environment do |_t, args|
    unless args[:project_identifier]
      puts "Usage: rake gitlab_integration:remove[project_identifier]"
      exit 1
    end

    project = Project.find_by(identifier: args[:project_identifier])

    unless project
      puts "Error: Project '#{args[:project_identifier]}' not found"
      exit 1
    end

    config = GitlabConfiguration.find_by(project:)

    if config
      config.destroy
      puts "✓ GitLab configuration removed for project '#{project.name}'"
    else
      puts "No GitLab configuration found for project '#{project.name}'"
    end
  end
end

