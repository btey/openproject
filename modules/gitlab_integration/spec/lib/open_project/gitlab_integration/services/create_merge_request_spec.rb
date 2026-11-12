# frozen_string_literal: true

require "spec_helper"
require_module_spec_helper

RSpec.describe OpenProject::GitlabIntegration::Services::CreateMergeRequest do
  let(:user) { create(:user) }
  let(:project) { create(:project) }
  let(:work_package) { create(:work_package, project:, subject: "Test Feature") }
  let(:gitlab_config) do
    instance_double(
      GitlabConfiguration,
      configured?: true,
      gitlab_url: "https://gitlab.example.com",
      project_identifier: "test/repo",
      access_token: "test-token"
    )
  end

  let(:service) { described_class.new(work_package:, user:, private_link: false) }

  before do
    allow(GitlabConfiguration).to receive(:for_project).with(project).and_return(gitlab_config)
  end

  describe "#call" do
    context "when GitLab is not configured" do
      before do
        allow(gitlab_config).to receive(:configured?).and_return(false)
      end

      it "returns a failure" do
        result = service.call
        expect(result).to be_failure
        expect(result.message).to eq("GitLab not configured for this project")
      end
    end

    context "when branch creation succeeds" do
      let(:branch_response) { instance_double(Net::HTTPCreated, is_a?: true, code: "201") }
      let(:mr_response) do
        instance_double(
          Net::HTTPSuccess,
          is_a?: true,
          body: { id: 1, web_url: "https://gitlab.example.com/test/repo/-/merge_requests/1" }.to_json
        )
      end

      before do
        allow_any_instance_of(Net::HTTP).to receive(:request).and_return(branch_response, mr_response)
      end

      it "creates a branch and merge request successfully" do
        result = service.call
        expect(result).to be_success
        expect(result.result).to have_key("id")
      end
    end

    context "when branch already exists" do
      let(:branch_exists_response) do
        instance_double(
          Net::HTTPBadRequest,
          code: "400",
          body: { message: "Branch already exists" }.to_json,
          message: "Bad Request"
        )
      end

      context "and an open MR exists with that branch" do
        let(:existing_mr) do
          {
            id: 1,
            web_url: "https://gitlab.example.com/test/repo/-/merge_requests/1",
            state: "opened",
            source_branch: "user-story/op-#{work_package.id}-test-feature"
          }
        end
        let(:check_mr_response) do
          instance_double(
            Net::HTTPSuccess,
            is_a?: true,
            body: [existing_mr].to_json
          )
        end

        before do
          # First call: branch creation fails
          # Second call: check for existing MR
          allow_any_instance_of(Net::HTTP).to receive(:request)
            .and_return(branch_exists_response, check_mr_response)
        end

        it "returns the existing merge request" do
          result = service.call
          expect(result).to be_success
          expect(result.result).to eq(existing_mr)
          expect(result.reused).to be true
        end
      end

      context "and no open MR exists" do
        let(:check_mr_response) do
          instance_double(
            Net::HTTPSuccess,
            is_a?: true,
            body: [].to_json
          )
        end
        let(:delete_response) { instance_double(Net::HTTPSuccess, is_a?: true, code: "204") }
        let(:branch_success_response) { instance_double(Net::HTTPCreated, is_a?: true, code: "201") }
        let(:mr_success_response) do
          instance_double(
            Net::HTTPSuccess,
            is_a?: true,
            body: { id: 2, web_url: "https://gitlab.example.com/test/repo/-/merge_requests/2" }.to_json
          )
        end

        before do
          # Sequence: branch creation fails -> check MR (empty) -> delete branch -> create branch -> create MR
          allow_any_instance_of(Net::HTTP).to receive(:request)
            .and_return(
              branch_exists_response,
              check_mr_response,
              delete_response,
              branch_success_response,
              mr_success_response
            )
        end

        it "deletes the old branch and creates a new one" do
          result = service.call
          expect(result).to be_success
          expect(result.result).to have_key("id")
        end
      end

      context "and branch cannot be deleted" do
        let(:check_mr_response) do
          instance_double(
            Net::HTTPSuccess,
            is_a?: true,
            body: [].to_json
          )
        end
        let(:delete_failed_response) { instance_double(Net::HTTPBadRequest, is_a?: false, code: "400") }
        let(:branch_with_suffix_response) { instance_double(Net::HTTPCreated, is_a?: true, code: "201") }
        let(:mr_success_response) do
          instance_double(
            Net::HTTPSuccess,
            is_a?: true,
            body: { id: 3, web_url: "https://gitlab.example.com/test/repo/-/merge_requests/3" }.to_json
          )
        end

        before do
          # Sequence: branch creation fails -> check MR (empty) -> delete fails -> create with suffix -> create MR
          allow_any_instance_of(Net::HTTP).to receive(:request)
            .and_return(
              branch_exists_response,
              check_mr_response,
              delete_failed_response,
              branch_with_suffix_response,
              mr_success_response
            )
        end

        it "creates a branch with timestamp suffix" do
          result = service.call
          expect(result).to be_success
          expect(result.result).to have_key("id")
        end
      end
    end

    context "when merge request creation fails" do
      let(:branch_response) { instance_double(Net::HTTPCreated, is_a?: true, code: "201") }
      let(:mr_failed_response) do
        instance_double(
          Net::HTTPBadRequest,
          is_a?: false,
          body: { message: "Invalid parameters" }.to_json,
          message: "Bad Request"
        )
      end

      before do
        allow_any_instance_of(Net::HTTP).to receive(:request).and_return(branch_response, mr_failed_response)
      end

      it "returns a failure" do
        result = service.call
        expect(result).to be_failure
        expect(result.message).to include("Failed to create merge request")
      end
    end
  end

  describe "branch naming" do
    context "with different work package types" do
      it "uses the work package type in the branch name" do
        bug = create(:type, name: "Bug")
        work_package.type = bug
        expect(service.send(:branch_name)).to start_with("bug/op-#{work_package.id}")
      end

      it "handles multi-word work package types" do
        feature = create(:type, name: "User Story")
        work_package.type = feature
        expect(service.send(:branch_name)).to start_with("user-story/op-#{work_package.id}")
      end

      it "lowercases and sanitizes the type name" do
        custom = create(:type, name: "Custom Feature Type")
        work_package.type = custom
        expect(service.send(:branch_name)).to start_with("custom-feature-type/op-#{work_package.id}")
      end
    end

    context "with different work package subjects" do
      it "sanitizes special characters in subject" do
        work_package.subject = "Fix issue #123 & update docs"
        expect(service.send(:branch_name)).to match(/op-\d+-fix-issue-123-and-update-docs/)
      end

      it "truncates long subjects" do
        work_package.subject = "A" * 100
        branch_name = service.send(:branch_name)
        # Should be truncated to 40 characters after parameterize
        expect(branch_name.length).to be <= 60 # type + /op- + id + - + 40 chars
      end
    end
  end
end
