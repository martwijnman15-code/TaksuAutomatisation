<?php

use Illuminate\Support\Facades\Route;

use App\Http\Controllers\CoffeeController;
use App\Http\Controllers\OrderController;

Route::middleware([
    'auth:sanctum',
    'throttle:60,1',
])->group(function () {

    Route::apiResource(
        'coffees',
        CoffeeController::class
    );

    Route::apiResource(
        'orders',
        OrderController::class
    );

});