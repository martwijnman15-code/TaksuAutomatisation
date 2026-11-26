<?php

namespace Tests\Feature;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Foundation\Testing\WithFaker;
use Tests\TestCase;

class OrderTest extends TestCase
{
    public function test_(): void
    {
        Order::factory()->create();

        $response = $this->postJson('/api/coffees', [
            'name' => 'Latte',
            'price' => 20
        ]);

        $response->assertUnprocessable();

        $response->assertJsonValidationErrors(['name']);
    }
}
