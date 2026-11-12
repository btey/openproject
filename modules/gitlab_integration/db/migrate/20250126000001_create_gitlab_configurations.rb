# frozen_string_literal: true

class CreateGitlabConfigurations < ActiveRecord::Migration[7.1]
  def change
    create_table :gitlab_configurations do |t|
      t.references :project, null: false, foreign_key: true, index: { unique: true }
      t.string :gitlab_url
      t.string :project_identifier
      t.text :access_token

      t.timestamps
    end
  end
end

