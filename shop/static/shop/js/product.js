(function(angular, undefined) {
'use strict';

// module: django.shop, TODO: move this into a summary JS file
var djangoShopModule = angular.module('django.shop.product', ['ui.bootstrap']);

djangoShopModule.controller('AddToCartCtrl', ['$scope', '$http', '$window', '$modal',
                                               function($scope, $http, $window, $modal) {
	var updateUrl = $window.location.pathname + '/add-to-cart' + $window.location.search;

	this.loadContext = function() {
		$http.get(updateUrl).success(function(context) {
			console.log('loaded product:');
			console.log(context);
			$scope.context = context;
		}).error(function(msg) {
			console.error('Unable to get context: ' + msg);
		});
	}

	$scope.updateContext = function() {
		$http.post(updateUrl, $scope.context).success(function(context) {
			console.log('loaded product:');
			console.log(context);
			$scope.context = context;
		}).error(function(msg) {
			console.error('Unable to update context: ' + msg);
		});
	}

	$scope.addToCart = function(cart_url) {
		$modal.open({
			templateUrl: 'AddToCartModalDialog.html',
			controller: 'ModalInstanceCtrl',
			resolve: {
				modal_context: function() {
					return {cart_url: cart_url, context: $scope.context};
				}
			}
		}).result.then(function(next_url) {
			console.log(next_url);
		});
	}

}]);

djangoShopModule.controller('ModalInstanceCtrl', ['$scope', '$http', '$modalInstance', 'modal_context',
                                        function($scope, $http, $modalInstance, modal_context) {
	console.log(modal_context);
	$scope.proceed = function(next_url) {
		$http.post(modal_context.cart_url, $scope.context).success(function() {
			$modalInstance.close(next_url);
		}).error(function() {
			// TODO: tell us something went wrong
			$modalInstance.dismiss('cancel');
		});
	};

	$scope.cancel = function () {
		$modalInstance.dismiss('cancel');
	};

	$scope.context = angular.copy(modal_context.context);
}]);


// Directive <add-to-cart>
// handle dialog box on the product's detail page to add a product to the cart
djangoShopModule.directive('addToCart', function() {
	return {
		restrict: 'EAC',
		controller: 'AddToCartCtrl',
		link: function(scope, element, attrs, AddToCartCtrl) {
			AddToCartCtrl.loadContext();
		}
	};
});

})(window.angular);
