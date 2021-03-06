define([
  'app',
  'utils/sortBuildList'
], function(app, sortBuildList) {
  'use strict';

  return {
    parent: 'project_details',
    url: 'sources/:source_id/',
    templateUrl: 'partials/project-source-details.html',
    controller: function($scope, $http, sourceData, buildList, Collection) {
      $scope.source = sourceData.data;
      $scope.builds = new Collection($scope, buildList.data, {
        sortFunc: sortBuildList,
        limit: 100
      });
    },
    resolve: {
      sourceData: function($http, $stateParams, projectData) {
        return $http.get('/api/0/projects/' + projectData.id + '/sources/' + $stateParams.source_id + '/');
      },
      buildList: function($http, $stateParams, projectData) {
        return $http.get('/api/0/projects/' + projectData.id + '/sources/' + $stateParams.source_id + '/builds/');
      }
    }
  };
});
