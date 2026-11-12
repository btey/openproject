# frozen_string_literal: true

class AddAuthorNameToGitlabIssuesAndMergeRequests < ActiveRecord::Migration[7.1]
  def change
    add_column :gitlab_issues, :gitlab_author_name, :string
    add_column :gitlab_merge_requests, :gitlab_author_name, :string
  end
end

