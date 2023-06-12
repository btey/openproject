import {
    IHalResourceLink,
    IHalResourceLinks,
  } from 'core-app/core/state/hal-resource';
  import { ID } from '@datorama/akita';
  
  export interface ISnippet {
    id:string;
    name:string;
    textToCopy:() => string
  }
  
  export interface IGitlabUserResource {
    avatarUrl:string;
    htmlUrl:string;
    login:string;
  }
  
  export interface IGitlabPipelineResource {
    appOwnerAvatarUrl:string;
    completedAt:string;
    conclusion:string;
    detailsUrl:string;
    htmlUrl:string;
    name:string;
    outputSummary:string;
    outputTitle:string;
    startedAt:string;
    status:string;
  }
  
  export interface IGitlabMergeRequestResourceLinks extends IHalResourceLinks {
    gitlabUser:IHalResourceLink;
    mergedBy?:IHalResourceLink;
    checkRuns?:IHalResourceLink[];
  }
  
  export interface IGitlabMergeRequestResourceEmbedded {
    githubUser:IGitlabUserResource;
    mergedBy?:IGitlabUserResource;
    pipelines:IGitlabPipelineResource[];
  }
  
  export interface IGitlabMergeRequest {
    id:ID;
    additionsCount?:number;
    body?:{
      format?:string;
      raw?:string;
      html?:string;
    },
    changedFilesCount?:number;
    commentsCount?:number;
    createdAt?:string;
    deletionsCount?:number;
    draft?:boolean;
    gitlabUpdatedAt?:string;
    htmlUrl:string;
    labels?:string[];
    merged?:boolean;
    mergedAt?:string;
    number?:number;
    repository:string;
    repositoryHtmlUrl:string;
    reviewCommentsCount?:number;
    state?:string;
    title:string;
    updatedAt?:string;
  
    _links:IGitlabMergeRequestResourceLinks;
    _embedded:IGitlabMergeRequestResourceEmbedded;
  }