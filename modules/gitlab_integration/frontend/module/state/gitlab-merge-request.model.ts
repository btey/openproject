import {
  IHalResourceLink,
  IHalResourceLinks,
} from 'core-app/core/state/hal-resource';
import { ID } from '@datorama/akita';


export interface ISnippet {
  id:string;
  name:string;
  textToCopy:()=>string
}

export interface IGitlabUserResource {
  avatarUrl:string;
  htmlUrl:string;
  login:string;
}

export interface IGitlabPipelineResource {
  userAvatarUrl:string;
  completedAt:string;
  detailsUrl:string;
  htmlUrl:string;
  name:string;
  startedAt:string;
  status:string;
  ci_details:string[];
  username:string;
  commitId:string;
}

export interface IGitlabMergeRequestResourceLinks extends IHalResourceLinks {
  gitlabUser:IHalResourceLink;
  mergedBy?:IHalResourceLink;
  pipelines?:IHalResourceLink[];
}

export interface IGitlabMergeRequestResourceEmbedded {
  gitlabUser:IGitlabUserResource;
  mergedBy?:IGitlabUserResource;
  pipelines:IGitlabPipelineResource[];
}

export interface IGitlabMergeRequest {
  body?:{
    format?:string;
    raw?:string;
    html?:string;
  },
  createdAt?:string;
  draft?:boolean;
  gitlabUpdatedAt?:string;
  htmlUrl:string;
  id?:number;
  labels?:string[];
  merged?:boolean;
  mergedAt?:string;
  // mergedBy?:IGitlabUserResource;
  number?:number;
  repository:string;
  state?:string;
  title:string;
  updatedAt?:string;
  // gitlabUser?:IGitlabUserResource;
  // pipelines?:IGitlabPipelineResource[];

  _links:IGitlabMergeRequestResourceLinks;
  _embedded:IGitlabMergeRequestResourceEmbedded;
}
