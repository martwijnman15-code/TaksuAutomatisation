<?php

namespace Tests\Feature;

use App\Models\Coffee;
use App\Models\Order;
use App\Models\CoffeeOrder;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Foundation\Testing\WithFaker;
use Tests\TestCase;

class CoffeeOrderTest extends TestCase
{
    /**
     * A basic feature test example.
     */
    public function test_if_coffee_forgein_id_is_numeric(): void
    {
        $coffee = Coffee::factory()->create([
            'name' => 'Teh Tarik',
            'description' => 'Teh, Susu',
            'is_coffee' => false
        ]);

        $order = Order::factory()->create([
            'code' => '1',
            'price' => 20000.00,
            'costumer_name' => 'Yusuf'
        ]);

        $coffee_order = CoffeeOrder::factory()->create([
            'coffee_id' => 'dnekjef',
            'order_id' => 1,
        ]);

        $response->assertUnprocessable();

        $response->assertJsonValidationErrors(['coffee_id']);
    }

    public function test_if_order_forgein_id_is_numeric(): void
    {
        $coffee = Coffee::factory()->create([
            'name' => 'Teh Tarik',
            'description' => 'Teh, Susu',
            'is_coffee' => false
        ]);

        $order = Order::factory()->create([
            'code' => '1',
            'price' => 20000.00,
            'costumer_name' => 'Yusuf'
        ]);

        $coffee_order = CoffeeOrder::factory()->create([
            'coffee_id' => 1,
            'order_id' => 'wfjfe',
        ]);

        $response->assertUnprocessable();

        $response->assertJsonValidationErrors(['order_id']);
    }
}
