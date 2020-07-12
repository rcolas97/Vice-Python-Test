import psycopg2


def get_job_statistics(job_id):
    return test_logic(job_id)


def _get_postgres_connection():
    return psycopg2.connect(host="localhost", port="5432", dbname="vice", user="postgres", password="rosny")


# making test runs and things of the like
def test_logic(job_id):
    res = {}  # the final output
    orders = {}  # the orders dictionary
    conn = _get_postgres_connection()
    cursor = conn.cursor()

    # First pull information from the JOBS table
    cursor.execute("SELECT * from jobs where id = {}".format(job_id))

    # Fill in output dictionary with proper values associated with the Job iD
    job = cursor.fetchone()
    res['job_name'] = job[1]
    res['expected_revenue'] = float(job[2])
    res['total_revenue'] = round(0.0, 2)
    res['revenue_target_met'] = False
    res['month_of_service_count'] = 1
    res['orders'] = orders

    # Now must grab the orders from revenue entries and update total rev while also adding to orders dictionary
    cursor.execute("SELECT * from revenue_entries where job_id = {}".format(job_id))
    r = cursor.fetchone()

    date_log = {}
    total_ecpm_raw = 0
    n = 0
    total_impressions = 0

    while r is not None:

        if float(r[4]) == 0.0:  # if the impressions is 0 then we cannot calculate an eCPM
            eCPM = 0.0
        else:
            eCPM = round(float(r[5]) / float(r[4]) * 1000.0, 2)  # revenue / impressions * 1000

        res['total_revenue'] += float(r[5])  # add the revenue of each row to the main dictionary's total revenue

        if r[1] in orders:  # if the order # is already in orders, then update the values associated with order #
            orders[r[1]]['total_revenue'] += round(float(r[5]), 2)
            orders[r[1]]['average_ecpm'] = round((total_ecpm_raw + eCPM) / n, 2)
            total_impressions += float(r[4])
            orders[r[1]]['total_ecpm'] = round((orders[r[1]]['total_revenue'] / total_impressions) * 1000.0, 2)
            n += 1

        else:  # if the order # is not in orders, then create a new key:value entry in orders
            orders[r[1]] = {"order_name": r[2],
                            "total_revenue": float(r[5]),
                            "average_ecpm": eCPM,
                            "total_ecpm": eCPM}

            n = 1
            total_ecpm_raw = eCPM
            total_impressions = float(r[4])

        res['month_of_service_count'] = month_check(date_log, r[3])

        r = cursor.fetchone()  # fetch the next row

    if res['total_revenue'] >= res['expected_revenue']:  # if total revenue meets or exceeds expected then update the boolean value
        res['revenue_target_met'] = True

    res['total_revenue'] = round(res['total_revenue'], 2)  # for some reason, the third case will not round to 2 decimal places

    cursor.close()
    conn.close()
    return res


def month_check(date_log, date):  # checks for diff in months however no current logic for different years
    if date.year in date_log:
        if date.month in date_log[date.year]:
            return 1
        else:
            date_log[date.year].append(int(date.month))
            return max(date_log[date.year]) - min(date_log[date.year]) + 1
    else:
        date_log[date.year] = [int(date.month)]
        return 1


#print(test_logic(1))
#print(test_logic(2))
#print(test_logic(3))
