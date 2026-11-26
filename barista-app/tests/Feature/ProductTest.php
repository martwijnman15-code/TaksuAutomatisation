<?php

namespace Tests\Feature;

use App\Models\Coffee;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class CoffeeTest extends TestCase
{
    use RefreshDatabase;

    public function test_coffee_can_be_readed(): void
    {
        Coffee::factory()->count(3)->create();

        $response = $this->getJson('/api/coffees');

        $response->assertStatus(200);

        $response->assertJsonCount(3, 'data');

        $response->assertJsonStructure([
            'data' => [
                '*' => ['id', 'name', 'description', 'is_coffee']
            ]
        ]);
    }

    public function test_coffee_can_be_created(): void
    {
        $response = $this->postJson('/api/coffees', [
            'name' => 'Laptop',
            'price' => 1000,
            'is_coffee' => false
        ]);

        $response->assertStatus(201);

        $this->assertDatabaseHas('coffees', [
            'name' => 'Laptop',
            'price' => 1000,
        ]);

    }

    public function test_coffee_can_be_updated(): void
    {
        $coffee = Coffee::factory()->create([
            'name' => 'Teh Tarik',
            'description' => 'Teh, Susu',
            'is_coffee' => false
        ]);

        $response = $this->putJson(
            "/api/coffees/{$coffee->id}",
            [
                'name' => 'Es Teh Tarik',
            ]
        );

        $response->assertStatus(200);

        $this->assertDatabaseHas('coffees', [
            'id' => $coffee->id,
            'name' => 'Es Teh Tarik',
            'description' => 'Teh, Susu',
            'is_coffee' => false
        ]);
    }

    public function test_coffee_can_be_showed(): void
    {
        $coffee = Coffee::factory()->create([
            'name' => 'Teh Tarik',
            'description' => 'Teh, Susu',
            'is_coffee' => false
        ]);

        $response = $this->getJson('/api/coffees');

        $response->assertStatus(200);

        $response->assertJsonCount(1, 'data');

        $this->assertDatabaseHas('coffees', [
            'id' => $coffee->id,
            'name' => 'Es Teh Tarik',
            'description' => 'Teh, Susu',
            'is_coffee' => false
        ]);
    }

    public function test_coffee_can_be_deleted(): void
    {
        $coffee = Coffee::factory()->create([
            'name' => 'Teh Tarik',
            'description' => 'Teh, Susu',
            'is_coffee' => false
        ]);

        $response = $this->deleteJson(
            "/api/coffees/{$coffee->id}"
        );

        $response->assertNoContent();

        $this->assertDatabaseMissing('coffees', [
            'id' => $coffee->id,
        ]);
    }

    public function test_coffee_can_not_be_created_by_user(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)->postJson('/api/coffees', [
            'name' => 'Laptop',
            'price' => 1000,
            'is_coffee' => false
        ]);

        $response->assertForbidden();
    }

    public function test_coffee_can_not_be_updated_by_user(): void
    {
        $coffee = Coffee::factory()->create([
            'name' => 'Teh Tarik',
            'description' => 'Teh, Susu',
            'is_coffee' => false
        ]);

        $user = User::factory()->create();

        $response = $this->actingAs($user)->putJson(
            "/api/coffees/{$coffee->id}",
            [
                'name' => 'Es Teh Tarik',
            ]
        );

        $response->assertForbidden();
    }

    public function test_coffee_can_be_not_deleted_by_user(): void
    {
        $coffee = Coffee::factory()->create([
            'name' => 'Teh Tarik',
            'description' => 'Teh, Susu',
            'is_coffee' => false
        ]);

        $user = User::factory()->create();

        $response = $this->actingAs($user)->deleteJson(
            "/api/coffees/{$coffee->id}"
        );

        $response->assertForbidden();
    }
}