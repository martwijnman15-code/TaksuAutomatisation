<?php

namespace App\Services;

use App\Models\Coffee;

class CoffeeService
{
    public function create(array $data): Coffee
    {
        return Coffee::create($data);
    }

    public function update(Coffee $coffee, array $data): Coffee
    {
        $coffee->update($data);
        return $coffee->refresh();
    }

    public function show(Coffee $coffee): Coffee
    {
        return $coffee->show($coffee);
    }
}