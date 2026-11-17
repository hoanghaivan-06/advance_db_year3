use("shop")
db.orders.drop()

db.orders.insertOne({
  _id: 1001,
  customer: { name: "Linh", city: "Hanoi" },
  status: "paid",
  items: [
    { sku: "BK-01", title: "Python Basics", qty: 2, price: 12.5 },
    { sku: "BK-07", title: "SQL in Practice", qty: 1, price: 18.0 },
  ],
})

db.orders.insertMany([
  { _id: 1002, customer: { name: "Nam", city: "Da Nang" }, status: "shipped",
    items: [{ sku: "BK-03", title: "Data Viz", qty: 1, price: 22.0 }] },
  { _id: 1003, customer: { name: "Mai", city: "Hanoi" }, status: "paid",
    items: [{ sku: "BK-01", title: "Python Basics", qty: 1, price: 12.5 }],
    coupon: "WELCOME10" },   // only this document has a coupon field
])

db.orders.find({ status: "paid" })                         // WHERE status = 'paid'
db.orders.find({ "customer.city": "Hanoi" })               // dot notation reaches inside
db.orders.find({ "items.sku": "BK-01" })                   // matches inside arrays
db.orders.find({ status: "paid", coupon: { $exists: true } })
db.orders.find({ "items.price": { $gt: 20 } })             // $gt, $gte, $lt, $lte, $ne, $in
db.orders.find({ status: { $in: ["paid", "shipped"] } },
               { _id: 1, status: 1 })                      // projection: only these fields
  .sort({ _id: -1 })
  .limit(2)

db.orders.updateOne({ _id: 1001 }, { $set: { status: "shipped" } })
db.orders.updateMany({ status: "paid" }, { $set: { reviewed: false } })
db.orders.updateOne({ _id: 1002 }, { $push: { tags: "gift" } })     // append to an array
db.orders.updateOne({ _id: 1003 }, { $unset: { coupon: "" } })      // remove a field
db.orders.deleteOne({ _id: 1003 })

db.orders.aggregate([
  { $match: { status: { $in: ["paid", "shipped"] } } },        // WHERE
  { $unwind: "$items" },                                       // one document per item
  { $group: {                                                  // GROUP BY
      _id: "$items.sku",
      units: { $sum: "$items.qty" },
      revenue: { $sum: { $multiply: ["$items.qty", "$items.price"] } },
  } },
  { $sort: { revenue: -1 } },                                  // ORDER BY
  { $limit: 5 },
])

db.orders.createIndex({ "customer.city": 1, status: 1 })
db.orders.find({ "customer.city": "Hanoi", status: "paid" }).explain("executionStats")

// Exercises
// 1. Insert five orders with different shapes, then find all orders containing a given sku.
db.orders.insertMany([
  { _id: 2001, customer: { name: "An", city: "Hanoi" }, status: "paid",
    items: [{ sku: "BK-01", qty: 2, price: 12.5 }], coupon: "SALE10" },
  { _id: 2002, customer: { name: "Binh", city: "Hue" }, status: "shipped",
    items: [{ sku: "BK-02", qty: 1, price: 30.0 }], gift: true },
  { _id: 2003, customer: { name: "Chi", city: "Da Nang" }, status: "paid",
    items: [{ sku: "BK-01", qty: 3, price: 12.5 }], tags: ["urgent"] },
  { _id: 2004, customer: { name: "Dung", city: "Hanoi" }, status: "paid",
    items: [{ sku: "BK-07", qty: 1, price: 18.0 }], shipping_fee: 2.5 },
  { _id: 2005, customer: { name: "Ha", city: "Hue" }, status: "shipped",
    items: [{ sku: "BK-01", qty: 1, price: 12.5 }], note: "call before delivery" },
])
db.orders.find({ "items.sku": "BK-01" })

// 2. Write an aggregation that returns revenue per city.
db.orders.aggregate([
  { $unwind: "$items" },
  { $group: {
      _id: "$customer.city",
      revenue: { $sum: { $multiply: ["$items.qty", "$items.price"] } },
  } },
  { $sort: { revenue: -1 } },
])

// 3. Create an index and compare explain() before and after on 10,000 generated documents.
db.orders.dropIndexes()
const cities = ["Hanoi", "Da Nang", "Hue", "HCMC"]
const statuses = ["paid", "shipped", "pending"]
const docs = []
for (let i = 0; i < 10000; i++) {
  docs.push({
    customer: { name: "User" + i, city: cities[i % 4] },
    status: statuses[i % 3],
    items: [{ sku: "BK-01", qty: 1, price: 12.5 }],
  })
}
db.orders.insertMany(docs)

db.orders.find({ "customer.city": "Hanoi", status: "paid" }).explain("executionStats")
db.orders.createIndex({ "customer.city": 1, status: 1 })
db.orders.find({ "customer.city": "Hanoi", status: "paid" }).explain("executionStats")
