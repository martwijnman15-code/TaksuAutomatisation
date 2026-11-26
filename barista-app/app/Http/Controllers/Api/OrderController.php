<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Order;
use Illuminate\Http\Request;
use App\Http\Resources\OrderResource;

class OrderController extends Controller
{
    public function __construct(
        protected OrderService $service
    ) {}
    /**
     * Display a listing of the resource.
     */
    public function index()
    {
        return response()->json(OrderResource::collection(
            Order::all()
        ));
    }

    /**
     * Store a newly created resource in storage.
     */
    public function store(Request $request)
    {
        $data = $request->validate([
            'code' => 'required|string|max:255',
            'price' => 'required',
            'costumer_name' => 'required|string|max:255',
            'order_id' => 'required|integer',
        ]);

        return response()->json($this->service->create(
            $data
        ));
    }

    /**
     * Display the specified resource.
     */
    public function show(Order $order)
    {
        return response()->json($this->service->show(
            $order
        ));
    }

    /**
     * Update the specified resource in storage.
     */
    public function update(Request $request, Order $order)
    {
        $data = $request->validate([
            'code' => 'required|string|max:255',
            'price' => 'required',
            'costumer_name' => 'required|string|max:255',
            'order_id' => 'required|integer',
        ]);

        return response()->json($this->service->update(
            $data,
            $order
        ));
    }

    /**
     * Remove the specified resource from storage.
     */
    public function destroy(Order $order)
    {
        return response()->json($this->service->show(
            $order
        ));    
    }
}