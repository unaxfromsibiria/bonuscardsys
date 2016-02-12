// {% load common %}
var cardNumberSize = parseInt('{{ "CARD_NUMBER_SIZE"|settings_value }}');
var phoneRegs = [
		new RegExp('^[\\+]{1}[7]{1}\\d{10}$'),
		new RegExp('^[8]{1}\\d{10}$')
	],
	cardNumReg = new RegExp('^\\d{'+ cardNumberSize +'}$');


PageApplication.controller('ManagePageNavigation', function($scope, $http) {
	$scope.clientName = '';
	$scope.clientPhone = '';
	$scope.clientCardNum = '';
	$scope.clientPhoneValid = false;
	$scope.clientCardNumValid = false;
	$scope.oneCardIsSave = false;
	$scope.warnMsg = '';
	$scope.lockAction = false;

	$scope.goTo = function(url) {
		window.location = '' + url;
	}

	$scope.phoneIsValid = function(phone) {
		var isValid = false;
		for (var i = 0; i < phoneRegs.length; i ++) {
			if (phoneRegs[i].test(phone || '')) {
				isValid = true;
				break;
			}
		}
		$scope.clientPhoneValid = isValid;
		return isValid;
	}

	$scope.cardNumIsValid = function(num) {
		var isValid = cardNumReg.test(num || '');
		$scope.clientCardNumValid = isValid;
		return isValid;
	}

	$scope.sendCardData = function() {
		if ($scope.clientPhoneValid && $scope.clientCardNumValid) {
			$scope.warnMsg = '';
			$scope.lockAction = true;
			$http(requestSrc('{% url "add_card" %}', {
				'update': $scope.oneCardIsSave,
				'name': $scope.clientName,
				'phone': $scope.clientPhone,
				'card': $scope.clientCardNum
			}))
			.success(function(data) {
				$scope.lockAction = false;
				if (!!data.ok) {
					$scope.oneCardIsSave = true;
				} else {
					$scope.warnMsg = data.msg || data;
				}
			})
			.error(function(data) {
				$scope.lockAction = false;
			});
		} else {
			$scope.warnMsg = 'Заполните поля правильно!';
		}
	}
});
