import * as firebase from './firebase.ts';

console.log("Firebase module functions:", Object.keys(firebase));

export default firebase;
export const getAreas = firebase.getAreas;
export const getRoutesForAreas = firebase.getRoutesForAreas;
export const getRouteById = firebase.getRouteById;
export const getAreaById = firebase.getAreaById;
export const searchAreas = firebase.searchAreas;
export const getAreaTree = firebase.getAreaTree;
export const getPopularAreas = firebase.getPopularAreas; 