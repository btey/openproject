//-- copyright
// OpenProject is an open source project management software.
// Copyright (C) 2023 Ben Tey
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License version 3.
//
// OpenProject is a fork of ChiliProject, which is a fork of Redmine. The copyright follows:
// Copyright (C) 2006-2013 Jean-Philippe Lang
// Copyright (C) 2010-2013 the ChiliProject Team
// Copyright (C) the OpenProject GmbH
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
//
// See docs/COPYRIGHT.rdoc for more details.
//++

import { Component, inject } from '@angular/core';
import { OPContextMenuComponent } from 'core-app/shared/components/op-context-menu/op-context-menu.component';
import { OpContextMenuLocalsToken, OpContextMenuLocalsMap } from 'core-app/shared/components/op-context-menu/op-context-menu.types';
import { I18nService } from "core-app/core/i18n/i18n.service";

export type LinkType = 'public' | 'private';

export interface LinkTypeItem {
  type:LinkType;
  label:string;
  icon:string;
  isDefault:boolean;
}

export interface LinkTypeMenuLocals extends OpContextMenuLocalsMap {
  linkType:LinkType;
  onSelected:(linkType:LinkType) => void;
}

@Component({
  selector: 'link-type-menu',
  templateUrl: './link-type-menu.template.html',
  styleUrls: ['./styles/link-type-menu.sass'],
  standalone: false,
})
export class LinkTypeMenuComponent extends OPContextMenuComponent {
  private readonly I18n = inject(I18nService);

  public override locals = inject<LinkTypeMenuLocals>(OpContextMenuLocalsToken);

  public linkType:LinkType;
  public onSelected:(linkType:LinkType) => void;

  public override items:LinkTypeItem[];

  public text = {
    publicLink: this.I18n.t('js.gitlab_integration.link_type_menu.public_link'),
    privateLink: this.I18n.t('js.gitlab_integration.link_type_menu.private_link'),
    defaultLabel: this.I18n.t('js.gitlab_integration.link_type_menu.default_label'),
  };

  constructor() {
    super();

    this.linkType = this.locals.linkType;
    this.onSelected = this.locals.onSelected;

    this.items = [
      {
        type: 'public',
        label: this.text.publicLink,
        icon: 'icon-unlocked',
        isDefault: true,
      },
      {
        type: 'private',
        label: this.text.privateLink,
        icon: 'icon-locked',
        isDefault: false,
      },
    ];
  }

  public selectLinkType(item:LinkTypeItem):void {
    this.linkType = item.type;
    this.onSelected(item.type);
    this.service.close();
  }

  public isSelected(item:LinkTypeItem):boolean {
    return this.linkType === item.type;
  }
}

