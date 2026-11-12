# frozen_string_literal: true

#-- copyright
# OpenProject is an open source project management software.
# Copyright (C) the OpenProject GmbH
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License version 3.
#
# OpenProject is a fork of ChiliProject, which is a fork of Redmine. The copyright follows:
# Copyright (C) 2006-2013 Jean-Philippe Lang
# Copyright (C) 2010-2013 the ChiliProject Team
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
# See COPYRIGHT and LICENSE files for more details.
#++

module OpenIDConnect
  class ConfigurationMapper
    attr_reader :configuration

    def initialize(configuration)
      @configuration = configuration
    end

    def call! # rubocop:disable Metrics/AbcSize
      options = configuration.deep_stringify_keys

      {
        "slug" => options["name"],
        "display_name" => options["display_name"].presence || "OpenID Connect",
        "oidc_provider" => oidc_provider(options),
        "client_id" => options["identifier"],
        "client_secret" => options["secret"],
        "issuer" => options["issuer"],
        "host" => options["host"],
        "port" => options["port"],
        "scheme" => options["scheme"],
        "claims" => extract_claims(options["claims"]),
        "tenant" => options["tenant"],
        "post_logout_redirect_uri" => options["post_logout_redirect_uri"],
        "limit_self_registration" => options["limit_self_registration"],
        "use_graph_api" => options["use_graph_api"],
        "acr_values" => options["acr_values"],
        "scope" => extract_scope(options["scope"]),
        "authorization_endpoint" => extract_url(options, "authorization_endpoint"),
        "token_endpoint" => extract_url(options, "token_endpoint"),
        "userinfo_endpoint" => extract_url(options, "userinfo_endpoint"),
        "end_session_endpoint" => extract_url(options, "end_session_endpoint"),
        "jwks_uri" => extract_url(options, "jwks_uri"),
        "grant_types_supported" => options["grant_types_supported"],
        "mapping_login" => options.dig("attribute_map", "login"),
        "mapping_email" => options.dig("attribute_map", "email"),
        "mapping_first_name" => options.dig("attribute_map", "first_name"),
        "mapping_last_name" => options.dig("attribute_map", "last_name"),
        "mapping_admin" => options.dig("attribute_map", "admin"),
        # CUSTOM CHANGE (BEGIN): fix boolean cast for `sync_groups`.
        # Upstream compared against the literal string "true", but ENV-sourced
        # configuration is already YAML-parsed into a real boolean by
        # Settings::Definition.extract_value_from_env before it reaches here
        # (e.g. `true == "true"` is `false` in Ruby). That silently forced
        # sync_groups to `false` for every ENV-configured provider, regardless
        # of the value set in OPENPROJECT_OPENID__CONNECT_<NAME>_SYNC__GROUPS.
        # ActiveModel::Type::Boolean handles both the real-boolean (ENV/seed)
        # path and a raw "true"/"false" string (tests, API) path correctly.
        # Revert to plain `options["sync_groups"]` (or remove) if upstream
        # fixes this properly - re-check on next merge.
        "sync_groups" => ActiveModel::Type::Boolean.new.cast(options["sync_groups"]),
        # CUSTOM CHANGE (END)
        "groups_claim" => options["groups_claim"],
        # CUSTOM CHANGE (BEGIN): allow filtering/renaming synced groups via ENV.
        # Upstream has no ENV mapping at all for `group_prefixes`/`group_regexes`,
        # and the Admin UI disables both fields once a provider is ENV-seeded
        # (see GroupMappingForm `disabled: provider.seeded_from_env?`), leaving
        # no way to configure filtering for ENV-managed providers. Both are
        # stored as `:json` arrays on the model (see Provider#group_matchers),
        # so we pass the ENV-parsed array through as-is, same as the existing
        # `grant_types_supported` mapping above. Set via e.g.:
        #   OPENPROJECT_OPENID__CONNECT_ENTRA_GROUP__PREFIXES: '["OP-", "PROJ-"]'
        #   OPENPROJECT_OPENID__CONNECT_ENTRA_GROUP__REGEXES: '["^OP-(.+)$"]'
        # `group_prefixes` takes precedence over `group_regexes` if both are set.
        # Remove this block if upstream adds native ENV support - re-check on
        # next merge.
        "group_prefixes" => options["group_prefixes"],
        "group_regexes" => options["group_regexes"]
        # CUSTOM CHANGE (END)
      }.compact
    end

    private

    def extract_claims(claims_value)
      case claims_value
      when Hash
        claims_value.to_json
      else
        claims_value.to_s
      end
    end

    def extract_scope(value)
      return if value.blank?

      case value
      when Array
        value.join(" ")
      else
        value
      end
    end

    def oidc_provider(options)
      case options["name"]
      when /azure/
        "microsoft_entra"
      when /google/
        "google"
      else
        "custom"
      end
    end

    def extract_url(options, key)
      value = options[key]
      return value if value.blank? || value.start_with?("http")

      unless value.start_with?("/")
        raise ArgumentError.new("Provided #{key} '#{value}' needs to be http(s) URL or path starting with a slash.")
      end

      # Allow returning the value as is for built-in providers
      # with fixed host names
      if oidc_provider(options) != "custom"
        return value
      end

      URI
        .join(base_url(options), value)
        .to_s
    end

    def base_url(options)
      raise ArgumentError.new("Missing host in configuration") unless options["host"]

      URI::Generic.build(
        host: options["host"],
        port: options["port"],
        scheme: options["scheme"] || "https"
      ).to_s
    end
  end
end
