import eric_client
import test_utils
import wan

#this tests part 2, but what about part 1
#for part 1, just change from delimiter to making something go over max size. 

def test_delimiter_at_end_without_fin(middlebox_module,is_testing_part1):
    if is_testing_part1:
        # print("test_delimiter_at_end_without_fin does not test simple_test")
        first_client2_block = "a" * 2000
        second_client2_block = "a" * 6000
        first_expected_bytes = 0
        second_expected_bytes = 8000
    else:
        first_client2_block = "a" * 2000
        second_client2_block = " straight chin suggestive of resolution pushed t"
        first_expected_bytes = 0
        second_expected_bytes = 2048
    middlebox1 = middlebox_module.WanOptimizer()
    middlebox2 = middlebox_module.WanOptimizer()
    wide_area_network = wan.Wan(middlebox1, middlebox2)

    # Iniitialize client connected to middlebox 1.
    client1_address = "1.2.3.4"
    client1_output_filename = "{}_output".format(client1_address)
    client1 = eric_client.EricClient(
        client1_address, middlebox1, client1_output_filename)

    # Initialize 2 clients connected to middlebox 2.
    client2_address = "5.6.7.8"
    client2_output_filename = "{}_output".format(client2_address)
    client2 = eric_client.EricClient(
        client2_address, middlebox2, client2_output_filename)

    client3_address = "5.6.7.9"
    client3_output_filename = "{}_output".format(client3_address)
    client3 = eric_client.EricClient(
        client3_address, middlebox2, client3_output_filename)

    # Send part of a block from client 1 to client 2.
    
    client1.send_data(first_client2_block, client2_address)
    #tests whether we have not recieved anything
    test_utils.verify_data_sent_equals_data_received("", client2_output_filename)
    bytes_sent = wide_area_network.get_total_bytes_sent()
    print('bytes sent 1')
    print(bytes_sent)
    if bytes_sent != first_expected_bytes:
        raise Exception("not correct number of bytes")

    # Now send some more data to client 2.
    
    client1.send_data(second_client2_block, client2_address)
    if client2.received_fin:
        raise Exception("Client 2 received the fin too early")
    #make sure data is correct, we do not have buffer, we just send everything
    test_utils.verify_data_sent_equals_data_received(
        first_client2_block + second_client2_block, client2_output_filename)

    bytes_sent = wide_area_network.get_total_bytes_sent()
    print('bytes sent 2')
    print(bytes_sent)
    if bytes_sent != second_expected_bytes:
        raise Exception("not correct number of bytes")


    # Close the client 2 stream.
    client1.send_fin(client2_address)
    if not client2.received_fin:
        raise Exception("Client 2 didnt't receive the fin")
    test_utils.verify_data_sent_equals_data_received(
        first_client2_block + second_client2_block, client2_output_filename)

def test_delimiter_in_middle_with_fin_after(middlebox_module,is_testing_part1):
    if is_testing_part1:
        first_client2_block = "a" * 2000
        second_client2_block = "a" * 8000
        second_client2_block_segment = "a" * 6000
        third_client2_block = "a" * 2000
    else:
        first_client2_block = "a" * 2000
        second_client2_block = "a long, straight chin suggestive of resolution pushed to the length of obstinacy"
        second_client2_block_segment = "a long, straight chin suggestive of resolution pushed t"
        third_client2_block = "wow"

    middlebox1 = middlebox_module.WanOptimizer()
    middlebox2 = middlebox_module.WanOptimizer()
    wide_area_network = wan.Wan(middlebox1, middlebox2)

    # Iniitialize client connected to middlebox 1.
    client1_address = "new_client_1"
    client1_output_filename = "{}_output".format(client1_address)
    client1 = eric_client.EricClient(
        client1_address, middlebox1, client1_output_filename)

    # Initialize 2 clients connected to middlebox 2.
    client2_address = "new_client_2"
    client2_output_filename = "{}_output".format(client2_address)
    client2 = eric_client.EricClient(
        client2_address, middlebox2, client2_output_filename)


    # Send part of a block from client 1 to client 2.
    client1.send_data(first_client2_block, client2_address)
    #tests whether we have not recieved anything
    test_utils.verify_data_sent_equals_data_received("", client2_output_filename)
    bytes_sent = wide_area_network.get_total_bytes_sent()
    print('bytes sent 1')
    print(bytes_sent)
    if bytes_sent != 0:
        raise Exception("not correct number of bytes")

    # Now send some more data to client 2.
    client1.send_data(second_client2_block, client2_address)
    if client2.received_fin:
        raise Exception("Client 2 received the fin too early")
    #make sure data is correct, we do not have buffer, we just send everything
    test_utils.verify_data_sent_equals_data_received(
        first_client2_block + second_client2_block_segment, client2_output_filename)
    bytes_sent = wide_area_network.get_total_bytes_sent()
    print('bytes sent 2')
    print(bytes_sent)
    if bytes_sent != len(first_client2_block + second_client2_block_segment):
        raise Exception("not correct number of bytes")


    # Close the client 2 stream.
    client1.send_data_with_fin(third_client2_block, client2_address)
    if not client2.received_fin:
        raise Exception("Client 2 didnt't receive the fin")
    test_utils.verify_data_sent_equals_data_received(
        first_client2_block + second_client2_block + third_client2_block, client2_output_filename)
    bytes_sent = wide_area_network.get_total_bytes_sent()
    print('bytes sent 3')
    print(bytes_sent)
    if bytes_sent != len(first_client2_block + second_client2_block + third_client2_block):
        raise Exception("not correct number of bytes")

def test_delimiter_at_end_with_fin(middlebox_module,is_testing_part1):
    if is_testing_part1:
        first_client2_block = "a" * 2000
        second_client2_block = "a" * 6000
        first_expected_bytes = 0
        second_expected_bytes = 8000
    else:
        first_client2_block = "a" * 2000
        second_client2_block = " straight chin suggestive of resolution pushed t"
        first_expected_bytes = 0
        second_expected_bytes = 2048
    middlebox1 = middlebox_module.WanOptimizer()
    middlebox2 = middlebox_module.WanOptimizer()
    wide_area_network = wan.Wan(middlebox1, middlebox2)

    # Iniitialize client connected to middlebox 1.
    client1_address = "1.2.3.4"
    client1_output_filename = "{}_output".format(client1_address)
    client1 = eric_client.EricClient(
        client1_address, middlebox1, client1_output_filename)

    # Initialize 2 clients connected to middlebox 2.
    client2_address = "5.6.7.8"
    client2_output_filename = "{}_output".format(client2_address)
    client2 = eric_client.EricClient(
        client2_address, middlebox2, client2_output_filename)

    client3_address = "5.6.7.9"
    client3_output_filename = "{}_output".format(client3_address)
    client3 = eric_client.EricClient(
        client3_address, middlebox2, client3_output_filename)

    # Send part of a block from client 1 to client 2.
    client1.send_data(first_client2_block, client2_address)
    #tests whether we have not recieved anything
    test_utils.verify_data_sent_equals_data_received("", client2_output_filename)
    bytes_sent = wide_area_network.get_total_bytes_sent()
    print('bytes sent 1')
    print(bytes_sent)
    if bytes_sent != first_expected_bytes:
        raise Exception("not correct number of bytes")


    # Now send some more data to client 2.
    client1.send_data_with_fin(second_client2_block, client2_address)
    bytes_sent = wide_area_network.get_total_bytes_sent()
    print('bytes sent 2')
    print(bytes_sent)
    if bytes_sent != second_expected_bytes:
        raise Exception("not correct number of bytes")

    # Close the client 2 stream.
    if not client2.received_fin:
        raise Exception("Client 2 didnt't receive the fin")

    #make sure data is correct, we do not have buffer, we just send everything
    test_utils.verify_data_sent_equals_data_received(
        first_client2_block + second_client2_block, client2_output_filename)

def test_right_partitions(middlebox_module,is_testing_part1):
    """
    This function is a test of Aisha's example

    So in example you've given, the window will progress like this...
    [0:4] ---> found a block
    [5:9] ----> found a block
    and I would have the following two blocks. 'aaaaa' and 'aaaaa'
     
    let's say if the string was 'bbbaaaaaaaaaaaaaaa'
    the window will progress as follows:
    [0:4]
    [1:5]
    [2:6]
    [3:7] ---> found a block = 'bbbaaaaa'
    [8:12] ---> found a block = 'aaaaa'
    [13:17] ---->found a block. = 'aaaaa'

    except that I will use the delimiter " straight chin suggestive of resolution pushed t" 
    instead. 
    """
    if is_testing_part1:
        delimit = "b" * 8000
        first_expected_bytes = 16020 #one 8000 byte block for 
        second_expected_bytes = 16080
        third_expected_bytes = 16100
        first_client2_block = "a" * 2000 + delimit[:6000] + delimit + delimit
        second_client2_block = delimit
    else:
        delimit = " straight chin suggestive of resolution pushed t"
        first_expected_bytes = 2116
        second_expected_bytes = 2176
        third_expected_bytes = 2196
        first_client2_block = "a" * 2000 + delimit + delimit + delimit
        second_client2_block = delimit
    
    middlebox1 = middlebox_module.WanOptimizer()
    middlebox2 = middlebox_module.WanOptimizer()
    wide_area_network = wan.Wan(middlebox1, middlebox2)

    # Iniitialize client connected to middlebox 1.
    client1_address = "1.2.3.4"
    client1_output_filename = "{}_output".format(client1_address)
    client1 = eric_client.EricClient(
        client1_address, middlebox1, client1_output_filename)

    # Initialize 2 clients connected to middlebox 2.
    client2_address = "5.6.7.8"
    client2_output_filename = "{}_output".format(client2_address)
    client2 = eric_client.EricClient(
        client2_address, middlebox2, client2_output_filename)

    # Send part of a block from client 1 to client 2.
    client1.send_data(first_client2_block, client2_address)
    #tests whether we recieved right thing
    test_utils.verify_data_sent_equals_data_received(
        first_client2_block, client2_output_filename)
    bytes_sent = wide_area_network.get_total_bytes_sent()
    print('bytes sent 1')
    print(bytes_sent)
    if bytes_sent != first_expected_bytes:
        raise Exception("not correct number of bytes")


    #send again
    client1.send_data(first_client2_block,client2_address)
    #tests whether we recieved right thing
    test_utils.verify_data_sent_equals_data_received(
        first_client2_block + first_client2_block, client2_output_filename)

    bytes_sent = wide_area_network.get_total_bytes_sent()
    print('bytes sent 2')
    print(bytes_sent)
    if bytes_sent != second_expected_bytes:
        raise Exception("not correct number of bytes")

    # Now send some more data to client 2.
    client1.send_data_with_fin(second_client2_block, client2_address)

    # Close the client 2 stream.
    if not client2.received_fin:
        raise Exception("Client 2 didnt't receive the fin")

    #make sure data is correct, we do not have buffer, we just send everything
    test_utils.verify_data_sent_equals_data_received(
        first_client2_block + first_client2_block + second_client2_block, client2_output_filename)

    bytes_sent = wide_area_network.get_total_bytes_sent()
    print('bytes sent 3')
    print(bytes_sent)
    if bytes_sent != third_expected_bytes:
        raise Exception("not correct number of bytes")
