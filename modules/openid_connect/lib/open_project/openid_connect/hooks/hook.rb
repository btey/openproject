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

module OpenProject::OpenIDConnect
  module Hooks
    class Hook < OpenProject::Hook::Listener
      ##
      # Once the user has signed in and has an oidc session
      # we want to map that to the internal session
      def user_logged_in(context)
        session = context.fetch(:session)
        ::OpenProject::OpenIDConnect::SessionMapper.handle_login(session)

        user = context.fetch(:user)

        access_token = session["omniauth.oidc_access_token"]

        if access_token
          OpenIDConnect::UserTokens::CreateService.new(user).call(
            access_token:,
            refresh_token: session["omniauth.oidc_refresh_token"],
            expires_in: session["omniauth.oidc_expires_in"],
            known_audiences: [OpenIDConnect::UserToken::IDP_AUDIENCE],
            # We clear previous tokens while adding this one to avoid keeping
            # stale tokens around (and to avoid piling up duplicate IDP tokens)
            # -> Fresh login causes fresh set of tokens
            clear_previous: true
          )
        end

        groups_claim = session["omniauth.oidc_groups"]
        OpenIDConnect::Groups::SyncService.new(user:).call(groups_claim:) unless groups_claim.nil?
      end

      ##
      # Called once omniauth has returned with an auth hash
      def omniauth_user_authorized(context)
        controller = context.fetch(:controller)
        session = controller.session
        provider = OpenIDConnect::Provider.find_by(slug: context.dig(:auth_hash, :provider))

        if provider
          session["omniauth.oidc_access_token"] = context.dig(:auth_hash, :credentials, :token)
          session["omniauth.oidc_refresh_token"] = context.dig(:auth_hash, :credentials, :refresh_token)
          session["omniauth.oidc_expires_in"] = parse_expires_in(context.dig(:auth_hash, :credentials, :expires_in))

          if provider.sync_groups
            # CUSTOM CHANGE (BEGIN) -- see #extract_groups_claim below for rationale.
            # Upstream only reads `raw_info`; we additionally fall back to the ID token.
            # If upstream changes this line during a merge, re-apply this call to
            # `extract_groups_claim` instead of the plain `raw_info` dig.
            session["omniauth.oidc_groups"] = extract_groups_claim(context, provider)
            # CUSTOM CHANGE (END)
          end
        end

        nil
      end

      private

      # CUSTOM CHANGE (BEGIN): local-only fix, not present upstream.
      #
      # Reason: Microsoft Entra ID never returns a "groups" claim from the
      # OIDC UserInfo endpoint (confirmed in Microsoft's own docs), so
      # `auth_hash[:extra][:raw_info]` -- which is only ever populated from that
      # endpoint by the omniauth-openid-connect gem -- is always missing groups
      # for Entra. Entra *does* include "groups" in the ID token, so we decode
      # that token ourselves as a fallback. Other IdPs (Keycloak, Okta, ...)
      # keep working unchanged since raw_info is tried first.
      #
      # On next upstream merge:
      #   - If `omniauth_user_authorized` still assigns
      #     `session["omniauth.oidc_groups"]` directly from
      #     `context.dig(:auth_hash, :extra, :raw_info, provider.groups_claim)`,
      #     keep this method and the call to it as-is.
      #   - If upstream adds native ID-token-based group support, remove this
      #     method and `#id_token_claims`, and revert to upstream's implementation.
      def extract_groups_claim(context, provider)
        groups = context.dig(:auth_hash, :extra, :raw_info, provider.groups_claim)
        return groups if groups.present?

        id_token_claims(context)&.fetch(provider.groups_claim, nil)
      end

      # CUSTOM CHANGE: local-only helper supporting #extract_groups_claim above.
      def id_token_claims(context)
        encoded_id_token = context.dig(:auth_hash, :credentials, :id_token)
        return nil if encoded_id_token.blank?

        # The strategy already verified this token's signature during callback_phase
        # (when verify_id_token is enabled); we only need to read its claims here.
        ::OpenIDConnect::ResponseObject::IdToken.decode(encoded_id_token, :skip_verification).raw_attributes
      rescue StandardError => e
        Rails.logger.error { "Failed to decode ID token to read groups claim: #{e.message}" }
        nil
      end
      # CUSTOM CHANGE (END)

      def parse_expires_in(expires_in)
        expires_in = expires_in.to_i
        return nil if expires_in.zero?

        expires_in
      end
    end
  end
end
