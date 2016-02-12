/**
 * 
 */

PageApplication.controller('AuthBlock', function($scope, $http) {
	$scope.passContent = '';
	$scope.warnMsg = '';
	$scope.okMsg = '';
	$scope.lockAction = true;
	$scope.addNum = function(num) {
		if ($scope.warnMsg) {
			$scope.warnMsg = '';
		}
		$scope.passContent = '' + $scope.passContent + num;
		$scope.lockAction = false;
	}

	$scope.authRequest = function() {
		$scope.lockAction = true;
		$http(requestSrc('{% url "auth_check" %}', {
			'password': sha256('' + PageData.keys['pub'] + $scope.passContent + PageData.keys['in']),
			'key': PageData.keys['pub']
		}))
		.success(function(data) {
			if (!!data.ok) {
				$scope.okMsg = data.msg;
				setTimeout(function() {
					window.location = '{% url "manage_page" %}';					
				}, 1000);
			} else {
				$scope.lockAction = false;
				$scope.warnMsg = data.msg || data;
			}
		})
		.error(function(data) {
			$scope.lockAction = false;
		});
	}
});
