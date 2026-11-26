<?php

namespace App\Services;

use App\Models\Order;

class OrderService
{
    public function create(array $data): Order
    {
        return Order::create($data);
    }

    public function update(Order $order, array $data): Order
    {
        $order->update($data);
        return $order->refresh();
    }

    public function show(Order $order): Order
    {
        return $order->show($order);
    }

    public function destroy(Order $order): Order
    {
        return $order->delete($order);
    }
}