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

import { Directive, EventEmitter, Input, Output } from '@angular/core';
import { OpContextMenuTrigger } from 'core-app/shared/components/op-context-menu/handlers/op-context-menu-trigger.directive';
import { LinkTypeMenuComponent, LinkType, LinkTypeMenuLocals } from './link-type-menu.component';

@Directive({
  selector: '[gitlabLinkTypeDropdown]',
  standalone: false,
})
export class LinkTypeDropdownDirective extends OpContextMenuTrigger {
  @Input('gitlabLinkTypeDropdown-linkType') public linkType:LinkType = 'public';
  @Output() public linkTypeChange = new EventEmitter<LinkType>();

  protected open(evt: Event | MouseEvent) {
    // stopPropagation is handled in the template via (click)="$event.stopPropagation()"
    // This prevents the button's click event from firing
    this.opContextMenu.show(this, evt as Event, LinkTypeMenuComponent);
  }

  public get locals():LinkTypeMenuLocals {
    return {
      linkType: this.linkType,
      onSelected: (linkType:LinkType) => {
        this.linkType = linkType;
        this.linkTypeChange.emit(linkType);
      },
      items: [], // Required by OpContextMenuLocalsMap interface
      contextMenuId: 'gitlab-integration-link-type-menu',
    };
  }
}

