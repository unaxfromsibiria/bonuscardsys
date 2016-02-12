// {% load common %}
var cardNumberSize = parseInt('{{ "CARD_NUMBER_SIZE"|settings_value }}'),
	bonusPolicy = {{ policy|tojs }};

PageApplication.controller('ManagePagePayment', function($scope, $http) {
	$scope.bonusPolicy = null;
	if (parseFloat(bonusPolicy.percent || 0) <= 0) {
		alert('На эту дату нет политики начисления бонусов!');
	} else {
		$scope.bonusPolicy = {
			'percent': parseFloat(bonusPolicy.percent),
			'limit': parseFloat(bonusPolicy.limit)
		};
	}

	$scope.serviceList = []; 
	$scope.selectedService = 0;
	$scope.number = '';
	$scope.clientData = null;
	$scope.payments = [];
	$scope.useSale = true;
	$scope.servicePrice = '';
	$scope.totalSum = 0.0;
	$scope.saleValue = 0;
	$scope.toPay = 0;
	$scope.msgWarning = '';
	$scope.msgFatal = '';
	$scope.paymentProblem = false;

	var startBonus = 0;

	function calcSum(sum) {
		$scope.totalSum = $scope.totalSum + sum;
	}

	function calcSale(useSale) {
		if (!!$scope.clientData) {			
			$scope.clientData.bonus = parseFloat(
					startBonus + $scope.totalSum * ($scope.bonusPolicy.percent / 100.0)).toFixed(2);
			var bonus = 0;
			if ($scope.payments.length > 1 || startBonus > 0) {
				bonus = parseFloat($scope.clientData.bonus);
			} else {
				bonus = startBonus;
			}
			var parts = parseInt(bonus/ $scope.bonusPolicy.limit);
			var value = ($scope.bonusPolicy.limit * parts);
			$scope.saleValue = value.toFixed(2);
			if (!useSale) {
				value = 0;
			}
			$scope.toPay = parseFloat($scope.totalSum - value);
		}
	}

	$scope.goTo = function(url) {
		window.location = '' + url;
	}

	$scope.$watch('number', function(num, old) {
		var number = '' + (num || '');
		if (number.length >= cardNumberSize && !$scope.clientData) {
			$http(requestSrc('{% url "get_client_data" %}', {'number': number}))
			.success(function(data) {
				if (!!data.ok) {
					$scope.clientData = data.client;
					startBonus = parseFloat(data.client.bonus || 0);
				}
			})
			.error(function(data) {
				
			});
		}
	});

	$scope.$watch('useSale', function(useSaleNow, old) {
		calcSale(useSaleNow);
	});

	$scope.addLine = function() {
		var pk = parseInt($scope.selectedService);
		if (pk > 0) {
			var price = parseFloat(parseFloat($scope.servicePrice).toFixed(2));
			var bonus = price * ($scope.bonusPolicy.percent / 100.0);
			var row = {
				'price': price.toFixed(2),
				'bonus': bonus.toFixed(2),
				'service': '',
				'service_pk': pk
			};
			for (var i = 0; i < $scope.serviceList.length; i++) {
				if ($scope.serviceList[i].id == pk) {
					row.service = '' + $scope.serviceList[i].name;
				}
			}
			$scope.payments.push(row);			
			calcSum(price)
			calcSale($scope.useSale);
		}
	}

	$scope.sendPayment =  function() {
		var request = {
			'card': $scope.clientData.card,
			'payments': angular.toJson($scope.payments),
			'use_sale': $scope.useSale
		};
		$http(requestSrc('{% url "make_payments" %}', request))
		.success(function(data) {
			if (!!data.ok) {
				startBonus = parseFloat(data.payment.bonus)
				$scope.clientData.bonus = startBonus.toFixed(2);
				$scope.payments = [];
				$scope.totalSum = 0.0;
				$scope.saleValue = 0;
				$scope.toPay = 0;
			} else {
				$scope.paymentProblem = true;
				$scope.msgWarning = '' + (data.msg || data);
			}
		})
		.error(function(err) {
			$scope.paymentProblem = true;
			$scope.msgFatal = 'Ошибка сервера: ' + ('' + err).slice(0, 50);
		});
	}

	$scope.servicePriceCorrect = function() {
		return (parseFloat($scope.servicePrice || 0) || 0) > 0;
	}

	$scope.removeService = function(index) {
		var price = parseFloat($scope.payments[index].price);
		$scope.payments.splice(index, 1);
		calcSum(-price);
		calcSale($scope.useSale);
	}

	$http.get('{% url "service_json" %}')
	.success(function(answer) {
		$scope.serviceList = answer.list;
	})
	.error(function(err) {
		$scope.serviceList = [];
	})
});
