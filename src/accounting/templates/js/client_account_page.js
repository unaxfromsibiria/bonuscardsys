PageApplication.controller('ClientLogonPage', function($scope, $http) {
	$scope.warnMsg = '';
	$scope.phone = '';
	$scope.card = '';
	$scope.clientData = null;
	$scope.payments = [];
	$scope.saleTotal = .0;

	$scope.$watch('phone', function() {
		if ($scope.warnMsg) {
			$scope.warnMsg = '';
		}
	});

	$scope.doEnter = function() {
		var phone = '' + $scope.phone;
		if (phone.length > 10) {
			phone = '' + phone.slice(phone.length - 10);
		}
		var request = {
			'client': sha256(phone + $scope.card)
		};
		$http(requestSrc('{% url "client_payments" %}', request))
		.success(function(data) {
			$scope.payments = [];
			$scope.saleTotal = .0;

			if (!!data.ok) {
				$scope.clientData = data.client;
				var item, i = 0;
				for (i; i < data.payments.length; i++) {
					item = data.payments[i];
					item.summa_sale = parseFloat(item.summa_sale);
					if (item.summa_sale <= 0) {
						item.summa_sale = null;
					} else {
						$scope.saleTotal += item.summa_sale;
						item.summa_sale = item.summa_sale.toFixed(2);
					}
					$scope.payments.push(item);
				}
			} else {
				$scope.warnMsg = '' + (data.msg || data);
			}
		})
		.error(function(err) {
			$scope.warnMsg = 'Ошибка сервера: ' + ('' + err).slice(0, 80);
			$scope.phone = '';
			$scope.card = '';
		});
	}
});
