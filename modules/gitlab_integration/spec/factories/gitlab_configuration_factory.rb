# frozen_string_literal: true

FactoryBot.define do
  factory :gitlab_configuration do
    project
    gitlab_url { "https://gitlab.com" }
    project_identifier { "test-group/test-project" }
    access_token { "glpat-test-token-#{SecureRandom.hex(10)}" }
  end
end

