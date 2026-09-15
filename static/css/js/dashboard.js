const ctx = document.getElementById("salesChart");

if (ctx) {

    new Chart(ctx, {

        type: "line",

        data: {

            labels: [
                "May",
                "June",
                "July",
                "August"
            ],

            datasets: [{

                label: "Revenue",

                data: [
                    150000,
                    80000,
                    60000,
                    50000
                ]

            }]

        },

        options: {

            responsive: true

        }

    });

}